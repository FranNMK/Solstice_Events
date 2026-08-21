"""
QR code generation service.

Generates a PNG QR code from an attendee's qr_code_id,
saves it to static/qrcodes/, and returns the relative URL path.
"""

import os
import qrcode
from qrcode.image.pil import PilImage

# Directory where QR PNGs are stored (created at startup by main.py via static mount)
_QR_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "qrcodes")


def generate_qr(qr_code_id: str) -> str:
    """
    Generate a QR code PNG encoding qr_code_id.
    Returns the URL path: /static/qrcodes/{qr_code_id}.png
    """
    os.makedirs(_QR_DIR, exist_ok=True)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_code_id)
    qr.make(fit=True)

    img: PilImage = qr.make_image(fill_color="black", back_color="white")
    file_path = os.path.join(_QR_DIR, f"{qr_code_id}.png")
    img.save(file_path)

    return f"/static/qrcodes/{qr_code_id}.png"
