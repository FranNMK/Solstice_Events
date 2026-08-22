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
    # Cloudinary — set to your cloudinary://key:secret@cloud_name URL.
    # When empty, files fall back to local static/ storage (local dev only).
    CLOUDINARY_URL: str = os.getenv("CLOUDINARY_URL", "")
    # Resend free-tier workaround: when set, ALL confirmation emails are
    # redirected to this address instead of the registrant's address.
    # Use your own verified Resend email during testing/staging.
    # Leave empty (or unset) in production once you have a verified domain.
    RESEND_TEST_TO: str = os.getenv("RESEND_TEST_TO", "")


settings = Settings()
