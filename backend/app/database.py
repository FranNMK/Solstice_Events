"""
Database engine and session configuration.

Async engine (aiomysql) is used by FastAPI route handlers.
Sync engine (pymysql) is used by the background badge worker thread,
which runs outside the async event loop.

SSL note: TiDB Cloud connection strings typically include ssl_ca=<path>.
On Windows the Linux default path (/etc/ssl/certs/...) does not exist, so
we substitute it with the certifi CA bundle automatically.
"""

import os
import re
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


_tidb_url = _fix_ssl_ca(settings.TIDB_URL)

# ---------------------------------------------------------------------------
# Async engine — used by FastAPI dependency get_db()
# ---------------------------------------------------------------------------
async_engine = create_async_engine(
    _tidb_url,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
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
# ---------------------------------------------------------------------------
# Convert mysql+aiomysql:// → mysql+pymysql:// for the sync driver.
_sync_url = _tidb_url.replace("mysql+aiomysql://", "mysql+pymysql://")

sync_engine = create_engine(
    _sync_url,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
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
