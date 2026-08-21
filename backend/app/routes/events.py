"""
Events router.

Public:
  GET  /events          — published events (customer + public)
  GET  /events/{id}     — single event detail (public)

Admin-only:
  POST /events          — create event
  PUT  /events/{id}     — update / publish event
  GET  /admin/events    — all events regardless of published status
  GET  /admin/events/{id}/attendees — all attendees for an event
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models import Event, Attendee, User
from app.schemas import EventCreate, EventUpdate, EventOut, AttendeeOut
from app.auth.utils import get_current_user, require_role

router = APIRouter(tags=["events"])


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------

@router.get("/events", response_model=List[EventOut])
async def list_published_events(db: AsyncSession = Depends(get_db)):
    """Returns all published events ordered by date ascending."""
    result = await db.execute(
        select(Event)
        .where(Event.is_published == True)  # noqa: E712
        .order_by(Event.date.asc())
    )
    return result.scalars().all()


@router.get("/events/{event_id}", response_model=EventOut)
async def get_event(event_id: str, db: AsyncSession = Depends(get_db)):
    event = (
        await db.execute(select(Event).where(Event.id == event_id))
    ).scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")
    return event


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------

@router.get("/admin/events", response_model=List[EventOut])
async def admin_list_all_events(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin")),
):
    """All events (published and unpublished) for admin management."""
    result = await db.execute(select(Event).order_by(Event.date.asc()))
    return result.scalars().all()


@router.post("/admin/events", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(
    body: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    event = Event(
        created_by=current_user["sub"],
        **body.model_dump(),
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.put("/admin/events/{event_id}", response_model=EventOut)
async def update_event(
    event_id: str,
    body: EventUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin")),
):
    event = (
        await db.execute(select(Event).where(Event.id == event_id))
    ).scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(event, field, value)

    await db.commit()
    await db.refresh(event)
    return event


@router.get("/admin/events/{event_id}/attendees", response_model=List[AttendeeOut])
async def list_event_attendees(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin")),
):
    """All attendees registered for a specific event."""
    result = await db.execute(
        select(Attendee)
        .where(Attendee.event_id == event_id)
        .order_by(Attendee.created_at.asc())
    )
    return result.scalars().all()
