import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    TIDB_URL: str = os.getenv("TIDB_URL", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change_me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    RESEND_FROM: str = os.getenv("RESEND_FROM", "onboarding@resend.dev")
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "change_me")
    BADGE_BASE_URL: str = os.getenv("BADGE_BASE_URL", "http://localhost:8000")
    # Cloudinary — used for QR code PNG storage; set to cloudinary://key:secret@cloud_name.
    # When empty, QR PNGs fall back to local static/ storage (local dev only).
    CLOUDINARY_URL: str = os.getenv("CLOUDINARY_URL", "")
    # Cloudflare R2 — used for badge PDF storage (S3-compatible).
    # When these are empty, badge PDFs fall back to local static/ storage.
    R2_ACCOUNT_ID: str = os.getenv("R2_ACCOUNT_ID", "")
    R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID", "")
    R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY", "")
    R2_BUCKET_NAME: str = os.getenv("R2_BUCKET_NAME", "")
    R2_PUBLIC_URL_BASE: str = os.getenv("R2_PUBLIC_URL_BASE", "")
    # Resend free-tier workaround: when set, ALL confirmation emails are
    # redirected to this address instead of the registrant's address.
    # Use your own verified Resend email during testing/staging.
    # Leave empty (or unset) in production once you have a verified domain.
    RESEND_TEST_TO: str = os.getenv("RESEND_TEST_TO", "")


settings = Settings()
