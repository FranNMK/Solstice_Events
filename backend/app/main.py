from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.auth.router import router as auth_router
from app.routes.events import router as events_router
from app.routes.attendees import router as attendees_router
from app.routes.checkin import router as checkin_router
from app.routes.webhooks import router as webhooks_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all database tables on startup (idempotent — skips existing tables)
    from app.database import Base, sync_engine
    import app.models  # noqa: F401 — registers all ORM models with Base
    Base.metadata.create_all(bind=sync_engine)
    logger.info("Database tables verified / created.")

    # TODO Phase 4: start background badge worker thread here
    yield


app = FastAPI(title="Solstice Events", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(auth_router)
app.include_router(events_router)
app.include_router(attendees_router)
app.include_router(checkin_router)
app.include_router(webhooks_router)


@app.get("/")
async def health_check():
    return {"status": "ok", "app": "Solstice Events"}
