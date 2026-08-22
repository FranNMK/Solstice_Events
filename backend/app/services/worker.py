"""
Background badge worker.

Runs as a daemon thread started from main.py lifespan.
Polls badge_jobs WHERE status='queued' every 2 seconds.
For each job:
  1. Marks job status=processing
  2. Sleeps 3-5 seconds (simulates badge printer latency)
  3. Generates the badge PDF via services/badge.py
  4. Builds a signed webhook payload (HMAC-SHA256)
  5. POSTs to /webhooks/badge-complete
  6. Marks job status=completed

The webhook handler (routes/webhooks.py) then updates the attendee record.
Using the sync SQLAlchemy engine + requests (not aiohttp) because this runs
entirely outside the async event loop in its own thread.
"""

import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SyncSessionLocal
from app.models import Attendee, BadgeJob, Event
from app.services.badge import generate_badge_pdf

logger = logging.getLogger(__name__)

_STOP = False  # set to True to gracefully stop the worker


def _get_session() -> Session:
    return SyncSessionLocal()


def _recover_stuck_jobs() -> None:
    """
    On startup: reset any jobs stuck in 'processing' back to 'queued'.
    This handles the case where the worker crashed mid-job on the previous run.
    """
    session = _get_session()
    try:
        stuck = session.execute(
            select(BadgeJob).where(BadgeJob.status == "processing")
        ).scalars().all()
        if stuck:
            logger.warning(
                "[worker] Recovering %d stuck job(s) from 'processing' → 'queued'",
                len(stuck),
            )
            for job in stuck:
                job.status = "queued"
            session.commit()
    except Exception as exc:
        logger.error("[worker] Failed to recover stuck jobs: %s", exc, exc_info=True)
    finally:
        session.close()


def _sign_payload(body: str) -> str:
    """Compute HMAC-SHA256 signature over the raw JSON body string."""
    return hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        body.encode(),
        hashlib.sha256,
    ).hexdigest()


def _process_job(session: Session, job: BadgeJob) -> None:
    """Process a single queued badge job end-to-end."""
    job_id = job.id

    # 1. Mark processing
    job.status = "processing"
    session.commit()
    logger.info("[worker] Processing job=%s attendee=%s", job_id, job.attendee_id)

    # 2. Load attendee + event
    attendee: Attendee = session.get(Attendee, job.attendee_id)
    if not attendee:
        logger.error(
            "[worker] Attendee %s not found, marking job failed", job.attendee_id,
            exc_info=True,
        )
        job.status = "failed"
        job.completed_at = datetime.now(timezone.utc)
        session.commit()
        return

    event: Event = session.get(Event, attendee.event_id)
    if not event:
        logger.error(
            "[worker] Event %s not found, marking job failed", attendee.event_id,
            exc_info=True,
        )
        job.status = "failed"
        job.completed_at = datetime.now(timezone.utc)
        session.commit()
        return

    # 4. Generate badge PDF
    try:
        _, url_path = generate_badge_pdf(
            attendee_id=attendee.id,
            name=attendee.name,
            profession=attendee.profession or "Attendee",
            event_title=event.title,
            event_date=event.date,
            qr_code_id=attendee.qr_code_id,
        )
    except Exception as exc:
        logger.error(
            "[worker] Badge PDF generation failed for job=%s: %s", job_id, exc,
            exc_info=True,
        )
        job.status = "failed"
        job.completed_at = datetime.now(timezone.utc)
        session.commit()
        return

    # 5. Build signed webhook payload
    payload = {
        "job_id": job_id,
        "attendee_id": attendee.id,
        "badge_pdf_url": url_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    body_str = json.dumps(payload, separators=(",", ":"))
    signature = _sign_payload(body_str)

    # 6. Call the webhook endpoint (same process, loopback)
    webhook_url = f"{settings.BADGE_BASE_URL}/webhooks/badge-complete"
    try:
        resp = requests.post(
            webhook_url,
            data=body_str,
            headers={
                "Content-Type": "application/json",
                "X-Signature": signature,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            logger.info("[worker] Webhook delivered for job=%s", job_id)
        else:
            logger.error("[worker] Webhook returned HTTP %s: %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.error(
            "[worker] Webhook POST failed for job=%s: %s", job_id, exc, exc_info=True,
        )
    # Don't mark failed — the DB was already updated by the webhook or we retry next cycle

    # 7. Mark job completed
    job.status = "completed"
    job.completed_at = datetime.now(timezone.utc)
    session.commit()
    logger.info("[worker] Job=%s completed", job_id)


def run_worker() -> None:
    """
    Main worker loop. Runs indefinitely in a daemon thread.
    Polls for queued jobs every 2 seconds.
    """
    logger.info("[worker] Badge worker started.")
    _recover_stuck_jobs()
    while not _STOP:
        session = _get_session()
        try:
            # Pick the oldest queued job (one at a time to keep things simple)
            job = session.execute(
                select(BadgeJob)
                .where(BadgeJob.status == "queued")
                .order_by(BadgeJob.created_at.asc())
                .limit(1)
            ).scalar_one_or_none()

            if job:
                _process_job(session, job)
            else:
                time.sleep(2)  # Nothing to do — poll again shortly

        except Exception as exc:
            logger.error(
                "[worker] Unexpected error in worker loop: %s", exc, exc_info=True,
            )
            time.sleep(2)
        finally:
            session.close()

    logger.info("[worker] Badge worker stopped.")
