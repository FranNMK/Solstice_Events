"""
Webhooks router.

POST /webhooks/badge-complete
  Called by the background badge worker after generating a badge PDF.
  Validates the HMAC-SHA256 X-Signature header, then updates the attendee:
    - status -> checked_in
    - badge_pdf_url -> the generated PDF path

Treated exactly like an external vendor callback:
  - No auth header (the signature IS the authentication)
  - Raw body is read and verified before parsing JSON
"""

import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.config import settings
from app.database import get_db
from app.models import Attendee

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _verify_signature(raw_body: bytes, signature: str) -> bool:
    """
    Recompute HMAC-SHA256 over raw request body and compare to provided signature.
    Uses hmac.compare_digest to prevent timing attacks.
    """
    expected = hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/badge-complete")
async def badge_complete(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Receive badge-complete callback from the background worker.
    Validates signature, then flips attendee status to checked_in.
    """
    # Read raw body BEFORE letting pydantic parse it (we need it for HMAC)
    raw_body = await request.body()
    signature = request.headers.get("X-Signature", "")

    if not signature:
        logger.warning("Webhook received with no X-Signature header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Signature header.",
        )

    if not _verify_signature(raw_body, signature):
        logger.warning("Webhook signature verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature.",
        )

    # Parse payload
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON payload: {exc}",
        )

    attendee_id   = payload.get("attendee_id")
    badge_pdf_url = payload.get("badge_pdf_url")
    job_id        = payload.get("job_id")

    if not attendee_id or not badge_pdf_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload must include attendee_id and badge_pdf_url.",
        )

    # Update attendee record
    attendee = (
        await db.execute(select(Attendee).where(Attendee.id == attendee_id))
    ).scalar_one_or_none()

    if not attendee:
        logger.error("Webhook: attendee %s not found (job=%s)", attendee_id, job_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendee {attendee_id} not found.",
        )

    attendee.status = "checked_in"
    attendee.badge_pdf_url = badge_pdf_url
    await db.commit()

    logger.info(
        "Attendee %s checked_in via webhook (job=%s badge=%s)",
        attendee_id, job_id, badge_pdf_url,
    )
    return {"ok": True, "attendee_id": attendee_id, "status": "checked_in"}
