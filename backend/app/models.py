"""
SQLAlchemy ORM models for Solstice Events.

Tables:
  users       — authentication + roles
  events      — published events (admin-managed)
  attendees   — registrations linking users → events
  badge_jobs  — async badge generation queue
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String, Text, Boolean, DateTime, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        SAEnum("customer", "admin", name="user_role"),
        nullable=False,
        default="customer",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    # relationships
    events: Mapped[list["Event"]] = relationship("Event", back_populates="creator")
    attendees: Mapped[list["Attendee"]] = relationship("Attendee", back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.email} role={self.role}>"


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------
class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    image_url: Mapped[str] = mapped_column(String(500), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    # relationships
    creator: Mapped["User"] = relationship("User", back_populates="events")
    attendees: Mapped[list["Attendee"]] = relationship("Attendee", back_populates="event")

    def __repr__(self) -> str:
        return f"<Event '{self.title}' published={self.is_published}>"


# ---------------------------------------------------------------------------
# Attendee
# ---------------------------------------------------------------------------
class Attendee(Base):
    __tablename__ = "attendees"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("events.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    profession: Mapped[str] = mapped_column(String(255), nullable=True)
    # qr_code_id is what gets encoded into the QR code and scanned at check-in
    qr_code_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=_uuid, index=True
    )
    status: Mapped[str] = mapped_column(
        SAEnum("registered", "pending", "checked_in", name="attendee_status"),
        nullable=False,
        default="registered",
    )
    badge_pdf_url: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    # relationships
    user: Mapped["User"] = relationship("User", back_populates="attendees")
    event: Mapped["Event"] = relationship("Event", back_populates="attendees")
    badge_jobs: Mapped[list["BadgeJob"]] = relationship("BadgeJob", back_populates="attendee")

    def __repr__(self) -> str:
        return f"<Attendee {self.name} event={self.event_id} status={self.status}>"


# ---------------------------------------------------------------------------
# BadgeJob
# ---------------------------------------------------------------------------
class BadgeJob(Base):
    __tablename__ = "badge_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    attendee_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("attendees.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        SAEnum("queued", "processing", "completed", "failed", name="job_status"),
        nullable=False,
        default="queued",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # relationships
    attendee: Mapped["Attendee"] = relationship("Attendee", back_populates="badge_jobs")

    def __repr__(self) -> str:
        return f"<BadgeJob attendee={self.attendee_id} status={self.status}>"
