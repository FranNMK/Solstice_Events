from contextlib import asynccontextmanager
import asyncio
import sys
import logging
import time
import uuid

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Solstice Events API starting up.")

    # ── R2 storage health-check ───────────────────────────────────────────
    # Log R2 configuration state at startup so Render logs make it obvious
    # whether badge PDFs will go to Cloudflare R2 or fall back to local disk.
    import os as _os
    _r2_vars = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY",
                "R2_BUCKET_NAME", "R2_PUBLIC_URL_BASE")
    _missing = [v for v in _r2_vars if not _os.getenv(v, "").strip()]
    if _missing:
        logger.warning(
            "R2 storage NOT configured — missing env vars: %s. "
            "Badge PDFs will fall back to local static/ (not persistent on Render).",
            ", ".join(_missing),
        )
    else:
        from app.services.r2_storage import _get_client
        _client = _get_client()
        if _client is None:
            logger.error("R2 env vars are set but boto3 client failed to initialise.")
        else:
            logger.info(
                "R2 storage configured — account=%s bucket=%s public_url=%s",
                _os.getenv("R2_ACCOUNT_ID", "")[:8] + "…",
                _os.getenv("R2_BUCKET_NAME", ""),
                _os.getenv("R2_PUBLIC_URL_BASE", ""),
            )

    import threading
    from app.services.worker import run_worker

    def _start_worker() -> threading.Thread:
        t = threading.Thread(target=run_worker, name="badge-worker", daemon=True)
        t.start()
        logger.info("Badge worker thread started (id=%s).", t.ident)
        return t

    worker_thread = _start_worker()

    async def _watchdog():
        """Restart the worker thread if it dies unexpectedly."""
        nonlocal worker_thread
        while True:
            await asyncio.sleep(30)
            if not worker_thread.is_alive():
                logger.warning(
                    "Badge worker thread is dead — restarting.",
                )
                worker_thread = _start_worker()

    watchdog_task = asyncio.create_task(_watchdog())

    yield

    watchdog_task.cancel()
    logger.info("Solstice Events API shut down.")


app = FastAPI(title="Solstice Events", lifespan=lifespan)


# ── Request logging middleware ────────────────────────────────────────────────
# Logs every inbound request and its response: method, path, status, latency.
# Each request gets a short request-id so correlated log lines are easy to find.
@app.middleware("http")
async def log_requests(request, call_next):
    req_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()
    logger.info(
        "[%s] → %s %s",
        req_id,
        request.method,
        request.url.path,
    )
    try:
        response = await call_next(request)
    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        logger.error(
            "[%s] ✗ %s %s — UNHANDLED EXCEPTION after %.0fms: %s",
            req_id,
            request.method,
            request.url.path,
            elapsed,
            exc,
            exc_info=True,
        )
        raise
    elapsed = (time.perf_counter() - start) * 1000
    level = logging.WARNING if response.status_code >= 400 else logging.INFO
    logger.log(
        level,
        "[%s] ← %s %s %d (%.0fms)",
        req_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response

# In production, ALLOWED_ORIGINS should be set to the frontend URL,
# e.g. "https://solstice-events.onrender.com".
# Falls back to "*" for local development when the env var is not set.
_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
_allowed_origins: list[str] = (
    [o.strip() for o in _raw_origins.split(",") if o.strip()]
    if _raw_origins != "*"
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
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
