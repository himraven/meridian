"""
Database engine and session management.

Supports SQLite (default) and PostgreSQL via DATABASE_URL env var.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# ── Database URL ───────────────────────────────────────────────────────────
# Default: SQLite in data/ directory
# Override with DATABASE_URL env var for PostgreSQL, etc.
from api.config import DATA_DIR as _CFG_DB_DIR
_default_db_path = _CFG_DB_DIR / "smartmoney.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_default_db_path}")

# ── Engine ─────────────────────────────────────────────────────────────────
_is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    # SQLite-specific: check_same_thread for multi-threaded FastAPI
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    # Connection pool settings
    pool_pre_ping=True,
    echo=False,
)

# Enable WAL mode for SQLite (better concurrent read/write)
if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
        cursor.close()


# ── Session ────────────────────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency: yields a DB session, auto-closes after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Base ───────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Init ───────────────────────────────────────────────────────────────────
def init_db():
    """Create all tables if they don't exist."""
    from api.db_models import (  # noqa: F401 — import to register models
        CongressTrade, ArkTrade, ArkHolding,
        DarkpoolAnomaly, InstitutionFiling, InstitutionHolding,
        Signal, TickerName, DataRefreshLog,
    )
    Base.metadata.create_all(bind=engine)
