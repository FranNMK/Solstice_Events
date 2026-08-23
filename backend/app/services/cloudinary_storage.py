"""
Cloudinary storage helper.

Provides two upload functions used by qr.py and badge.py:
  - upload_image(data: bytes, public_id: str) -> str   (returns CDN URL)
  - upload_pdf(file_path: str, public_id: str)  -> str   (returns CDN URL)

When CLOUDINARY_URL is not configured (local dev), both functions return
None and callers fall back to the local static/ path.

Cloudinary free tier limits:
  - 25 GB managed storage
  - 25 GB monthly bandwidth
  - Transformations, CDN delivery included
"""

import logging
import os

logger = logging.getLogger(__name__)

# Lazily configured — only import/configure when CLOUDINARY_URL is set
_configured = False


def _configure() -> bool:
    """
    Configure the cloudinary SDK from the CLOUDINARY_URL env var.
    Returns True if successfully configured, False otherwise.
    The cloudinary SDK reads CLOUDINARY_URL automatically when it is set.
    """
    global _configured
    if _configured:
        return True

    cloudinary_url = os.getenv("CLOUDINARY_URL", "")
    if not cloudinary_url or cloudinary_url.startswith("cloudinary://api_key"):
        return False  # placeholder / not set

    try:
        import cloudinary  # noqa: F401 — triggers auto-config from CLOUDINARY_URL env var
        _configured = True
        logger.info("Cloudinary configured from CLOUDINARY_URL.")
        return True
    except Exception as exc:
        logger.error("Failed to configure Cloudinary: %s", exc)
        return False


def upload_image(data: bytes, public_id: str) -> str | None:
    """
    Upload raw PNG bytes to Cloudinary under the 'solstice/qrcodes/' folder.

    Args:
        data:       Raw PNG image bytes.
        public_id:  Unique identifier (qr_code_id, no extension).

    Returns:
        The Cloudinary CDN URL, or None if Cloudinary is not configured.
    """
    if not _configure():
        return None

    import io
    import cloudinary.uploader

    try:
        result = cloudinary.uploader.upload(
            io.BytesIO(data),
            public_id=f"solstice/qrcodes/{public_id}",
            resource_type="image",
            format="png",
            overwrite=True,
            invalidate=True,
        )
        url: str = result["secure_url"]
        logger.info("QR uploaded to Cloudinary: %s", url)
        return url
    except Exception as exc:
        logger.error("Cloudinary image upload failed: %s", exc)
        return None


async def download_pdf_bytes(attendee_id: str) -> bytes | None:
    """
    Download badge PDF bytes from Cloudinary using API authentication.
    This bypasses any CDN delivery restrictions on the account.
    Returns raw PDF bytes, or None if Cloudinary is not configured.
    """
    if not _configure():
        return None

    import cloudinary.utils
    import time
    import httpx

    # Build a signed download URL using the API secret — this always works
    # regardless of CDN delivery type (authenticated/upload/private)
    url, _ = cloudinary.utils.cloudinary_url(
        f"solstice/badges/{attendee_id}.pdf",
        resource_type="raw",
        type="upload",
        secure=True,
        sign_url=True,
        expires_at=int(time.time()) + 300,  # 5 min is plenty
    )

    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        resp = await client.get(url)

    if resp.status_code == 200:
        return resp.content

    # Try authenticated delivery type as fallback
    url_auth, _ = cloudinary.utils.cloudinary_url(
        f"solstice/badges/{attendee_id}.pdf",
        resource_type="raw",
        type="authenticated",
        secure=True,
        sign_url=True,
        expires_at=int(time.time()) + 300,
    )
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        resp2 = await client.get(url_auth)

    if resp2.status_code == 200:
        return resp2.content

    logger.error(
        "download_pdf_bytes: both URL types returned non-200 for %s (upload=%s, auth=%s)",
        attendee_id, resp.status_code, resp2.status_code,
    )
    return None


def make_signed_url(attendee_id: str, expires_in: int = 3600) -> str | None:
    """
    Generate a signed Cloudinary URL for a badge PDF that bypasses
    account-level access restrictions. Valid for `expires_in` seconds (default 1h).
    Returns None if Cloudinary is not configured.
    """
    if not _configure():
        return None
    import time
    import cloudinary
    expiry = int(time.time()) + expires_in
    url, _ = cloudinary.utils.cloudinary_url(
        f"solstice/badges/{attendee_id}.pdf",
        resource_type="raw",
        type="upload",
        secure=True,        # force https:// — required on HTTPS pages (Mixed Content)
        sign_url=True,
        expires_at=expiry,
    )
    return url or None


def upload_pdf(file_path: str, public_id: str) -> str | None:
    """
    Upload a PDF file from disk to Cloudinary under 'solstice/badges/' folder.

    Args:
        file_path:  Absolute path to the local PDF file.
        public_id:  Unique identifier (attendee_id, no extension).

    Returns:
        The Cloudinary CDN URL, or None if Cloudinary is not configured.
    """
    if not _configure():
        return None

    import cloudinary.uploader

    try:
        result = cloudinary.uploader.upload(
            file_path,
            public_id=f"solstice/badges/{public_id}",
            resource_type="raw",   # 'raw' is required for non-image files like PDF
            type="upload",         # 'upload' = public delivery (default is 'authenticated' for raw)
            format="pdf",
            overwrite=True,
            invalidate=True,
        )
        url: str = result["secure_url"]
        logger.info("Badge PDF uploaded to Cloudinary: %s", url)
        return url
    except Exception as exc:
        logger.error("Cloudinary PDF upload failed: %s", exc)
        return None
