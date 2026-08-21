"""
Pydantic v2 request/response schemas for Solstice Events.

Organised by domain: Auth, Events, Attendees, CheckIn, Webhooks.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str = "customer"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("customer", "admin"):
            raise ValueError("role must be 'customer' or 'admin'")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str


class UserOut(BaseModel):
    id: str
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------
class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    date: datetime
    location: Optional[str] = None
    image_url: Optional[str] = None
    is_published: bool = False


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    is_published: Optional[bool] = None


class EventOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    date: datetime
    location: Optional[str] = None
    image_url: Optional[str] = None
    is_published: bool
    created_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Attendees
# ---------------------------------------------------------------------------
class AttendeeRegisterRequest(BaseModel):
    event_id: str
    name: str
    profession: Optional[str] = None


class AttendeeOut(BaseModel):
    id: str
    user_id: str
    event_id: str
    name: str
    profession: Optional[str] = None
    qr_code_id: str
    status: str
    badge_pdf_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AttendeeWithEventOut(BaseModel):
    """Attendee record with embedded event details — used on customer dashboard."""
    id: str
    user_id: str
    event_id: str
    name: str
    profession: Optional[str] = None
    qr_code_id: str
    status: str
    badge_pdf_url: Optional[str] = None
    created_at: datetime
    event: EventOut

    model_config = {"from_attributes": True}


class AttendeeStatusOut(BaseModel):
    """Lightweight status-only response used for polling."""
    id: str
    status: str
    badge_pdf_url: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Check-in
# ---------------------------------------------------------------------------
class CheckInRequest(BaseModel):
    qr_code_id: str


class CheckInResponse(BaseModel):
    already_checked_in: bool = False
    status: Optional[str] = None
    attendee_id: Optional[str] = None
    job_id: Optional[str] = None
    message: str = ""


# ---------------------------------------------------------------------------
# Webhook
# ---------------------------------------------------------------------------
class BadgeCompletePayload(BaseModel):
    job_id: str
    attendee_id: str
    badge_pdf_url: str
    timestamp: str
