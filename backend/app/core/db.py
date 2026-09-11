"""Database engine + session dependency.

Connects using the postgres/service-role connection string (DATABASE_URL),
which bypasses Supabase RLS. The backend is the only trusted writer.
"""
from __future__ import annotations

from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

# pool_pre_ping avoids stale-connection errors against Supabase's pooler.
# connect_timeout keeps startup/health checks fast-failing instead of hanging
# on an unreachable host (matters for Render cold starts as much as local dev).
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
    connect_args={"connect_timeout": 5},
)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a SQLModel Session."""
    with Session(engine) as session:
        yield session


def create_db_and_tables() -> None:
    """Dev convenience only — production schema is managed via Supabase migrations."""
    SQLModel.metadata.create_all(engine)
