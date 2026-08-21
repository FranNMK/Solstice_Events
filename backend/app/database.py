"""
Database engine and session configuration.

Async engine (aiomysql) is used by FastAPI route handlers.
Sync engine (pymysql) is used by the background badge worker thread,
which runs outside the async event loop.

SSL note: TiDB Cloud connection strings include ssl_ca=<path>.
- For the SYNC engine (pymysql): pass ssl_ca via the URL query param as before.
- For the ASYNC engine (aiomysql + Python 3.14): aiomysql passes SSL options as
  a plain dict, but Python 3.14 asyncio requires a real ssl.SSLContext. We strip
  ssl_ca from the async URL and build an SSLContext manually to pass via connect_args.
"""

import os
import re
import ssl
import certifi
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings


def _fix_ssl_ca(url: str) -> str:
    """Replace a non-existent ssl_ca path with the certifi bundle path."""
    def _replacer(m: re.Match) -> str:
        path = m.group(1)
        if not os.path.exists(path):
            return f"ssl_ca={certifi.where()}"
        return m.group(0)
    return re.sub(r"ssl_ca=([^&]+)", _replacer, url)


def _strip_ssl_params(url: str) -> str:
    """Remove ssl_ca (and any other ssl_*) query params from a URL string."""
    # Remove ssl_ca=... param and clean up dangling & or ?
    url = re.sub(r"[&?]ssl_ca=[^&]*", "", url)
    url = re.sub(r"[&?]ssl_verify_cert=[^&]*", "", url)
    # If we removed params and left a dangling ?, drop it
    url = re.sub(r"\?$", "", url)
    return url


def _build_ssl_context() -> ssl.SSLContext:
    """Build a proper SSLContext using the certifi CA bundle."""
    ctx = ssl.create_default_context(cafile=certifi.where())
    return ctx


# ---------------------------------------------------------------------------
# Async engine — used by FastAPI dependency get_db()
# aiomysql needs the SSLContext passed explicitly; strip ssl_ca from URL.
# ---------------------------------------------------------------------------
_async_url_base = _strip_ssl_params(settings.TIDB_URL)
_ssl_ctx = _build_ssl_context()

async_engine = create_async_engine(
    _async_url_base,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "connect_timeout": 30,
        "ssl": _ssl_ctx,
    },
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# Sync engine — used by the background worker thread (Phase 4)
# pymysql handles ssl_ca in the URL correctly via its own SSL logic.
# ---------------------------------------------------------------------------
_sync_url = _fix_ssl_ca(settings.TIDB_URL).replace("mysql+aiomysql://", "mysql+pymysql://")

sync_engine = create_engine(
    _sync_url,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"connect_timeout": 30},
)

SyncSessionLocal = sessionmaker(bind=sync_engine, autoflush=False, autocommit=False)


def get_sync_db():
    """Context manager — yields a sync DB session for the worker thread."""
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Declarative base — all ORM models inherit from this
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass
