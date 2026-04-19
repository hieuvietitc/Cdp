import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from cdp_shared.config import settings

# Pool sizing: each service gets its own engine instance (separate process).
# pool_size=20, max_overflow=30 → max 50 connections per service process.
# With PgBouncer in front (Phase 4), this can be tightened.
_POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", "20"))
_MAX_OVERFLOW = int(os.environ.get("DB_POOL_MAX_OVERFLOW", "30"))

engine = create_engine(
    settings.database_url,
    pool_size=_POOL_SIZE,
    max_overflow=_MAX_OVERFLOW,
    pool_pre_ping=True,
    # Recycle connections every 30 min to avoid stale TCP connections
    pool_recycle=1800,
    # Timeout waiting for a connection from the pool (seconds)
    pool_timeout=30,
    connect_args={
        "connect_timeout": 10,
        # Kill queries running longer than 60s at the DB level
        "options": "-c statement_timeout=60000",
    },
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
