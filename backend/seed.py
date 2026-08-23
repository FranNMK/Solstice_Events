"""
Seed script — populates TiDB with demo data for development/testing.

Run from the backend/ directory with the venv activated:
    python seed.py

Idempotent: skips users/events that already exist (matched by email / title).
"""

import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

# Ensure app package is importable
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
import bcrypt as _bcrypt

from app.config import settings
from app.database import Base, _fix_ssl_ca
import app.models as m  # registers all models

# ---------------------------------------------------------------------------
# Setup — reuse the same SSL-fix helper from database.py
# ---------------------------------------------------------------------------
_sync_url = _fix_ssl_ca(settings.TIDB_URL).replace("mysql+aiomysql://", "mysql+pymysql://")
engine = create_engine(_sync_url, echo=False, pool_pre_ping=True)
Session = sessionmaker(bind=engine)


def _hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def _uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Ensure tables exist
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)
print("[OK] Tables verified.")

# ---------------------------------------------------------------------------
# Seed users
# ---------------------------------------------------------------------------
ADMIN_EMAIL = "admin@solstice.dev"
DEMO_EMAIL = "demo@solstice.dev"

with Session() as session:
    # Admin user
    admin = session.execute(
        select(m.User).where(m.User.email == ADMIN_EMAIL)
    ).scalar_one_or_none()

    if admin is None:
        admin = m.User(
            id=_uuid(),
            email=ADMIN_EMAIL,
            hashed_password=_hash_password("admin123"),
            role="admin",
            created_at=datetime.now(timezone.utc),
        )
        session.add(admin)
        print(f"[OK] Created admin user: {ADMIN_EMAIL}")
    else:
        print(f"  Admin user already exists: {ADMIN_EMAIL}")

    # Customer / demo user
    customer = session.execute(
        select(m.User).where(m.User.email == DEMO_EMAIL)
    ).scalar_one_or_none()

    if customer is None:
        customer = m.User(
            id=_uuid(),
            email=DEMO_EMAIL,
            hashed_password=_hash_password("demo123"),
            role="customer",
            created_at=datetime.now(timezone.utc),
        )
        session.add(customer)
        print(f"[OK] Created demo customer: {DEMO_EMAIL}")
    else:
        print(f"  Demo customer already exists: {DEMO_EMAIL}")

    session.commit()
    # Re-fetch to get IDs after commit
    admin = session.execute(
        select(m.User).where(m.User.email == ADMIN_EMAIL)
    ).scalar_one()

# ---------------------------------------------------------------------------
# Seed events
# ---------------------------------------------------------------------------
DEMO_EVENTS = [
    {
        "title": "Nairobi Tech Summit 2025",
        "description": (
            "Kenya's premier technology conference bringing together developers, entrepreneurs, "
            "and innovators from across East Africa. A full day of keynotes, workshops, and "
            "networking covering AI, fintech, cloud computing, and the future of tech on the continent."
        ),
        "date": datetime.now(timezone.utc) + timedelta(days=14),
        "location": "Kenyatta International Convention Centre (KICC), Nairobi",
        "image_url": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&q=80",
        "is_published": True,
    },
    {
        "title": "Waanzilishi & Wawekezaji Forum",
        "description": (
            "An exclusive evening connecting Kenyan startup founders with local angel investors, "
            "venture capital partners, and development finance institutions. Pitch your idea, "
            "forge lasting partnerships, and navigate the East African funding landscape."
        ),
        "date": datetime.now(timezone.utc) + timedelta(days=30),
        "location": "The Alchemist Bar & Garden, Westlands, Nairobi",
        "image_url": "https://images.unsplash.com/photo-1511795409834-ef04bbd61622?w=800&q=80",
        "is_published": True,
    },
    {
        "title": "Ubunifu Design & UX Workshop",
        "description": (
            "A hands-on full-day workshop for Kenyan UX/UI designers and front-end engineers. "
            "Build a scalable design system from scratch, explore accessible design for African "
            "audiences, and master Figma-to-code workflows with local industry practitioners."
        ),
        "date": datetime.now(timezone.utc) + timedelta(days=7),
        "location": "iHub, 8th Floor, Senteu Plaza, Kilimani, Nairobi",
        "image_url": "https://images.unsplash.com/photo-1559028012-481c04fa702d?w=800&q=80",
        "is_published": True,
    },
]

with Session() as session:
    admin_id = session.execute(
        select(m.User.id).where(m.User.email == ADMIN_EMAIL)
    ).scalar_one()

    for ev_data in DEMO_EVENTS:
        existing = session.execute(
            select(m.Event).where(m.Event.title == ev_data["title"])
        ).scalar_one_or_none()

        if existing is None:
            event = m.Event(
                id=_uuid(),
                created_by=admin_id,
                created_at=datetime.now(timezone.utc),
                **ev_data,
            )
            session.add(event)
            print(f"[OK] Created event: {ev_data['title']}")
        else:
            print(f"  Event already exists: {ev_data['title']}")

    session.commit()

print("\n[DONE] Seed complete.")
print(f"  Admin login:    {ADMIN_EMAIL} / admin123")
print(f"  Customer login: {DEMO_EMAIL}  / demo123")
