from contextlib import asynccontextmanager
import asyncio
import sys
import logging

# aiomysql does not support the Windows IOCP ProactorEventLoop (Python 3.8+ default on Windows).
# Force the SelectorEventLoop so aiomysql SSL works on Windows.
# DeprecationWarning suppressed — can be removed once aiomysql gains native IOCP SSL support.
if sys.platform == "win32":
    import warnings as _w
    with _w.catch_warnings():
        _w.simplefilter("ignore", DeprecationWarning)
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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
    logger.info("Solstice Events API starting up.")

    # Start the background badge worker as a daemon thread
    import threading
    from app.services.worker import run_worker
    worker_thread = threading.Thread(target=run_worker, name="badge-worker", daemon=True)
    worker_thread.start()
    logger.info("Badge worker thread started.")

    yield

    logger.info("Solstice Events API shut down.")


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
