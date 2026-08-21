"""
QR code generation service.

Generates a PNG QR code from an attendee's qr_code_id.

Storage strategy (in priority order):
  1. Cloudinary — if CLOUDINARY_URL is configured, the PNG is generated
     in-memory and uploaded; returns a persistent CDN URL.
  2. Local static/ — fallback for local development when Cloudinary is
     not configured; saves to static/qrcodes/ and returns a /static/... path.

The badge.py service needs the QR image as a local file to embed it in the
PDF via reportlab. When Cloudinary is used, the PNG is also saved to a temp
file so badge.py can read it during the same worker job run.
"""

import io
import logging
import os
import tempfile

import qrcode
from qrcode.image.pil import PilImage

from app.services.cloudinary_storage import upload_image

logger = logging.getLogger(__name__)

_QR_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "qrcodes")


def generate_qr(qr_code_id: str) -> str:
    """
    Generate a QR code PNG encoding qr_code_id.

    Returns a URL string:
      - Cloudinary CDN URL  (https://res.cloudinary.com/...) if configured
      - /static/qrcodes/{qr_code_id}.png                     otherwise
    """
    # Build the QR image in memory first (works for both paths)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_code_id)
    qr.make(fit=True)

    img: PilImage = qr.make_image(fill_color="black", back_color="white")

    # Encode to bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    # Always save locally so badge.py can embed the image via reportlab
    os.makedirs(_QR_DIR, exist_ok=True)
    local_path = os.path.join(_QR_DIR, f"{qr_code_id}.png")
    with open(local_path, "wb") as f:
        f.write(png_bytes)

    # Try Cloudinary upload
    cdn_url = upload_image(png_bytes, qr_code_id)
    if cdn_url:
        return cdn_url

    # Fallback: serve from local static
    return f"/static/qrcodes/{qr_code_id}.png"
