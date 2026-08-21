"""
Check-in router.

POST /checkin  — admin-only
  Accepts a qr_code_id, validates it, and either:
    - Returns {already_checked_in: true} if status is pending or checked_in (duplicate-scan guard)
    - Sets status=pending, inserts a BadgeJob(queued), returns immediately (async pipeline start)

The entire check + update is wrapped in a SELECT FOR UPDATE equivalent using
a DB-level lock via with_for_update() to prevent race conditions on concurrent scans.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Attendee, BadgeJob
from app.schemas import CheckInRequest, CheckInResponse
from app.auth.utils import require_role

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/checkin", tags=["checkin"])


@router.post("", response_model=CheckInResponse)
async def check_in(
    body: CheckInRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin")),
):
    """
    Admin scans a QR code to check in an attendee.

    Duplicate-scan protection covers BOTH pending and checked_in states:
    - If already checked_in  → already_checked_in=True (no new job)
    - If already pending     → already_checked_in=True (first job still in flight)
    - If registered          → set pending, enqueue badge job, return immediately
    """
    # Lock the row for the duration of this transaction to prevent race conditions
    attendee = (
        await db.execute(
            select(Attendee)
            .where(Attendee.qr_code_id == body.qr_code_id)
            .with_for_update()
        )
    ).scalar_one_or_none()

    if not attendee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No attendee found for QR code: {body.qr_code_id}",
        )

    # Duplicate-scan guard — covers pending (job in flight) AND checked_in
    if attendee.status in ("pending", "checked_in"):
        msg = (
            "Already checked in."
            if attendee.status == "checked_in"
            else "Check-in already in progress (badge being generated)."
        )
        logger.info(
            "Duplicate scan blocked: attendee=%s status=%s", attendee.id, attendee.status
        )
        return CheckInResponse(
            already_checked_in=True,
            status=attendee.status,
            attendee_id=attendee.id,
            message=msg,
        )

    # Valid new check-in: mark pending and enqueue badge job atomically
    attendee.status = "pending"
    job = BadgeJob(attendee_id=attendee.id)
    db.add(job)
    await db.commit()
    await db.refresh(attendee)
    await db.refresh(job)

    logger.info(
        "Check-in queued: attendee=%s job=%s", attendee.id, job.id
    )
    return CheckInResponse(
        already_checked_in=False,
        status="pending",
        attendee_id=attendee.id,
        job_id=job.id,
        message="Check-in accepted. Badge generation in progress.",
    )
