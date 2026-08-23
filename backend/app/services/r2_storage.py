"""
Cloudflare R2 storage helper (S3-compatible via boto3).

Provides:
  upload_pdf(file_bytes: bytes, key: str) -> str | None

Returns the public URL of the uploaded file, or None if R2 is not configured.
The key should be a unique filename, e.g. "{attendee_id}.pdf".

Required environment variables:
  R2_ACCOUNT_ID          — Cloudflare account ID
  R2_ACCESS_KEY_ID       — R2 API token Access Key ID
  R2_SECRET_ACCESS_KEY   — R2 API token Secret Access Key
  R2_BUCKET_NAME         — Name of the R2 bucket
  R2_PUBLIC_URL_BASE     — Public URL base, e.g. https://pub-xxx.r2.dev
                           (or a custom domain bound to the bucket)
"""

import io
import logging
import os

logger = logging.getLogger(__name__)

_client = None  # lazy boto3 S3 client


def _get_client():
    """Return a cached boto3 S3 client pointed at the R2 endpoint."""
    global _client
    if _client is not None:
        return _client

    account_id = os.getenv("R2_ACCOUNT_ID", "")
    access_key = os.getenv("R2_ACCESS_KEY_ID", "")
    secret_key = os.getenv("R2_SECRET_ACCESS_KEY", "")

    if not (account_id and access_key and secret_key):
        return None  # R2 not configured

    try:
        import boto3

        _client = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="auto",
        )
        logger.info("R2 client initialised (account=%s)", account_id)
        return _client
    except Exception as exc:
        logger.error("Failed to initialise R2 client: %s", exc)
        return None


def upload_pdf(file_bytes: bytes, key: str) -> str | None:
    """
    Upload PDF bytes to R2 under the given key (e.g. "badges/{attendee_id}.pdf").

    Returns:
        The public URL (R2_PUBLIC_URL_BASE + "/" + key), or None on failure /
        when R2 is not configured.
    """
    client = _get_client()
    if client is None:
        return None

    bucket = os.getenv("R2_BUCKET_NAME", "")
    public_url_base = os.getenv("R2_PUBLIC_URL_BASE", "").rstrip("/")

    if not bucket or not public_url_base:
        logger.warning("R2_BUCKET_NAME or R2_PUBLIC_URL_BASE not set — skipping upload")
        return None

    try:
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=io.BytesIO(file_bytes),
            ContentType="application/pdf",
        )
        url = f"{public_url_base}/{key}"
        logger.info("Badge PDF uploaded to R2: %s", url)
        return url
    except Exception as exc:
        logger.error("R2 PDF upload failed (key=%s): %s", key, exc)
        return None
