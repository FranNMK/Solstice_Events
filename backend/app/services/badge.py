"""
Badge PDF generation service using reportlab.

Produces a card-style A6 badge PDF containing:
  - Attendee name (large, bold)
  - Profession (subtitle)
  - Event name + formatted date
  - QR code image (generated in-memory — NOT read from disk so Render's
    ephemeral filesystem cannot cause a missing-file failure)
  - Solstice Events branding

Storage strategy (in priority order):
  1. Cloudinary — PDF is written to a temp file, uploaded to Cloudinary,
     temp file is removed; returns a persistent CDN URL.
  2. Local static/badges/ — fallback for local dev; returns /static/... path.
"""

import io
import logging
import os
import tempfile
from datetime import datetime

import qrcode
from qrcode.image.pil import PilImage
from reportlab.lib.pagesizes import A6
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader

from app.services.cloudinary_storage import upload_pdf

logger = logging.getLogger(__name__)

# Brand colors
ORANGE = HexColor("#F97316")
NAVY   = HexColor("#1E2A4A")
LIGHT  = HexColor("#FFF7ED")
GRAY   = HexColor("#6B7280")

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")
_BADGES_DIR = os.path.join(_STATIC_DIR, "badges")


def _build_qr_image_reader(qr_code_id: str) -> ImageReader | None:
    """
    Generate the QR PNG in-memory and return an ImageReader for reportlab.
    Falls back to reading the local file if it happens to exist (local dev).
    Never fails — returns None if both paths fail, badge is drawn without QR.
    """
    # Prefer in-memory generation (works on Render with ephemeral disk)
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_code_id)
        qr.make(fit=True)
        img: PilImage = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return ImageReader(buf)
    except Exception as exc:
        logger.warning("In-memory QR generation failed, trying local file: %s", exc)

    # Fallback: local file (local dev)
    local_qr = os.path.join(os.path.dirname(__file__), "..", "static", "qrcodes",
                             f"{qr_code_id}.png")
    if os.path.exists(local_qr):
        try:
            return ImageReader(local_qr)
        except Exception as exc:
            logger.warning("Could not load local QR file: %s", exc)

    return None


def _draw_badge(file_path: str, name: str, profession: str,
                event_title: str, event_date: datetime, qr_code_id: str) -> None:
    """Draw the badge PDF to file_path using reportlab."""
    width, height = A6  # 105 x 148 mm ≈ 298 x 420 pts
    c = Canvas(file_path, pagesize=A6)

    # Background
    c.setFillColor(white)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Top accent bar
    bar_h = 14 * mm
    c.setFillColor(NAVY)
    c.rect(0, height - bar_h, width, bar_h, fill=1, stroke=0)

    # Brand name in bar
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width / 2, height - bar_h + 3 * mm, "SOLSTICE EVENTS")

    # Orange accent line below bar
    c.setStrokeColor(ORANGE)
    c.setLineWidth(2)
    c.line(8 * mm, height - bar_h - 1 * mm, width - 8 * mm, height - bar_h - 1 * mm)

    # Attendee name
    y_name = height - bar_h - 14 * mm
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 16)
    display_name = name if len(name) <= 24 else name[:22] + "..."
    c.drawCentredString(width / 2, y_name, display_name)

    # Profession
    y_prof = y_name - 7 * mm
    c.setFillColor(ORANGE)
    c.setFont("Helvetica-Bold", 9)
    display_prof = (profession or "Attendee")[:30]
    c.drawCentredString(width / 2, y_prof, display_prof.upper())

    # Divider
    y_div = y_prof - 5 * mm
    c.setStrokeColor(HexColor("#E5E7EB"))
    c.setLineWidth(0.5)
    c.line(8 * mm, y_div, width - 8 * mm, y_div)

    # QR Code — generated in-memory so no local-disk dependency on Render
    qr_size = 30 * mm
    qr_x    = (width - qr_size) / 2
    y_qr    = y_div - 5 * mm - qr_size

    qr_reader = _build_qr_image_reader(qr_code_id)
    if qr_reader:
        try:
            c.drawImage(qr_reader, qr_x, y_qr,
                        width=qr_size, height=qr_size, preserveAspectRatio=True)
        except Exception as exc:
            logger.warning("Could not embed QR image: %s", exc)
            c.setStrokeColor(GRAY)
            c.rect(qr_x, y_qr, qr_size, qr_size, fill=0)
    else:
        c.setStrokeColor(GRAY)
        c.rect(qr_x, y_qr, qr_size, qr_size, fill=0)

    # Event info
    y_event = y_qr - 9 * mm
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 9)
    event_display = event_title if len(event_title) <= 32 else event_title[:30] + "..."
    c.drawCentredString(width / 2, y_event, event_display)

    y_date = y_event - 5 * mm
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 8)
    date_str = event_date.strftime("%B %d, %Y") if event_date else ""
    c.drawCentredString(width / 2, y_date, date_str)

    # Bottom footer
    footer_h = 8 * mm
    c.setFillColor(LIGHT)
    c.rect(0, 0, width, footer_h, fill=1, stroke=0)
    c.setFillColor(ORANGE)
    c.setFont("Helvetica", 7)
    c.drawCentredString(width / 2, 2.5 * mm, "Connect  |  Experience  |  Celebrate")

    c.save()


def generate_badge_pdf(
    attendee_id: str,
    name: str,
    profession: str,
    event_title: str,
    event_date: datetime,
    qr_code_id: str,
) -> tuple[str, str]:
    """
    Generate a badge PDF for an attendee.

    Returns:
        (file_path, url_path)
          - file_path: absolute local path (temp or static/badges/)
          - url_path:  Cloudinary CDN URL  OR  /static/badges/{id}.pdf
    """
    # Try Cloudinary path: write to a named temp file, upload, then delete
    cdn_url = _try_cloudinary_upload(
        attendee_id, name, profession, event_title, event_date, qr_code_id
    )
    if cdn_url:
        # Return a dummy local path (worker only uses url_path for the webhook payload)
        return ("", cdn_url)

    # Fallback: persist to static/badges/
    os.makedirs(_BADGES_DIR, exist_ok=True)
    local_path = os.path.join(_BADGES_DIR, f"{attendee_id}.pdf")
    _draw_badge(local_path, name, profession, event_title, event_date, qr_code_id)
    logger.info("Badge PDF saved locally: %s", local_path)
    return (local_path, f"/static/badges/{attendee_id}.pdf")


def _try_cloudinary_upload(
    attendee_id: str,
    name: str,
    profession: str,
    event_title: str,
    event_date: datetime,
    qr_code_id: str,
) -> str | None:
    """
    Write PDF to a temp file, upload to Cloudinary, delete temp file.
    Returns the CDN URL on success, None if Cloudinary is not configured or upload fails.
    """
    tmp_path = None
    try:
        # Use a named temp file with .pdf suffix so Cloudinary detects the type
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name

        _draw_badge(tmp_path, name, profession, event_title, event_date, qr_code_id)
        cdn_url = upload_pdf(tmp_path, attendee_id)
        return cdn_url  # None if Cloudinary not configured
    except Exception as exc:
        logger.error("Cloudinary badge upload error: %s", exc)
        return None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
