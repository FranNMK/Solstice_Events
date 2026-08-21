"""
Email service — sends confirmation emails via Resend.

Graceful fallback: if RESEND_API_KEY is not configured, the email content
is logged to console instead of sent so the app works during development.
"""

import logging
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


def _format_date(dt: datetime) -> str:
    return dt.strftime("%A, %B %d, %Y at %I:%M %p UTC")


def send_confirmation_email(
    to: str,
    name: str,
    event_title: str,
    event_date: datetime,
    event_location: str,
    qr_url: str,
) -> None:
    """
    Send a registration confirmation email with event details and QR code link.
    Falls back to console logging if RESEND_API_KEY is not set.
    """
    subject = f"You're registered: {event_title}"
    formatted_date = _format_date(event_date)

    html_body = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, 'Segoe UI', sans-serif; max-width: 560px;
             margin: 0 auto; padding: 24px; color: #1E2A4A;">

  <div style="text-align: center; margin-bottom: 32px;">
    <h1 style="color: #F97316; margin: 0; font-size: 28px;">Solstice Events</h1>
    <p style="color: #6b7280; margin: 4px 0 0;">Connect &bull; Experience &bull; Celebrate</p>
  </div>

  <div style="background: #f7f8fa; border-radius: 12px; padding: 24px; margin-bottom: 24px;">
    <h2 style="margin: 0 0 8px; font-size: 20px;">You&rsquo;re registered, {name}!</h2>
    <p style="margin: 0; color: #57606a;">Here are your event details:</p>
  </div>

  <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
    <tr>
      <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb;
                 font-weight: 600; width: 120px;">Event</td>
      <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb;">{event_title}</td>
    </tr>
    <tr>
      <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb; font-weight: 600;">Date</td>
      <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb;">{formatted_date}</td>
    </tr>
    <tr>
      <td style="padding: 12px 0; font-weight: 600;">Location</td>
      <td style="padding: 12px 0;">{event_location or "TBD"}</td>
    </tr>
  </table>

  <div style="background: #fff7ed; border: 1px solid #fed7aa; border-radius: 8px;
              padding: 16px; margin-bottom: 24px; text-align: center;">
    <p style="margin: 0 0 8px; font-weight: 600; color: #c2410c;">Your Check-in QR Code</p>
    <p style="margin: 0; color: #57606a; font-size: 14px;">
      Log in to your dashboard to view and download your QR code.<br>
      Present it at the door to check in.
    </p>
  </div>

  <p style="color: #57606a; font-size: 13px; text-align: center; margin: 0;">
    Questions? Reply to this email or visit your dashboard.
  </p>

  <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
  <p style="color: #9ca3af; font-size: 12px; text-align: center; margin: 0;">
    &copy; Solstice Events &mdash; Connect &bull; Experience &bull; Celebrate
  </p>
</body>
</html>
"""

    if not settings.RESEND_API_KEY:
        # Graceful fallback — log to console during development
        logger.info("=== [EMAIL FALLBACK — RESEND_API_KEY not set] ===")
        logger.info("To:      %s", to)
        logger.info("Subject: %s", subject)
        logger.info("Event:   %s on %s at %s", event_title, formatted_date, event_location)
        logger.info("QR URL:  %s", qr_url)
        logger.info("=================================================")
        return

    try:
        import resend
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": settings.RESEND_FROM,
            "to": [to],
            "subject": subject,
            "html": html_body,
        })
        logger.info("Confirmation email sent to %s for event '%s'", to, event_title)
    except Exception as exc:
        # Never let email failure crash registration
        logger.error("Failed to send confirmation email to %s: %s", to, exc)
