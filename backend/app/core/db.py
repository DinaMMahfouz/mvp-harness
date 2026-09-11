"""Database engine + session dependency.

Supports two backends, chosen purely by the DATABASE_URL scheme:

  postgresql://...   Supabase (production, and local dev when the network allows it).
                     Connects with the postgres/service-role connection string,
                     which bypasses Supabase RLS. The backend is the only trusted
                     writer.

  sqlite:///...      Local file database, for development on networks that block
                     outbound Postgres ports. Supabase's pooler listens on 6543
                     (session mode: 5432); corporate firewalls commonly permit
                     only 443/80 outbound, which makes Supabase unreachable from
                     the machine regardless of credentials. SQLite needs no
                     network at all, so the app is fully exercisable offline.

The two backends are NOT interchangeable for every purpose — see
create_db_and_tables() below — but the ORM layer above this module is identical,
so services, routers and tests do not know or care which one is in use.
"""
from __future__ import annotations

from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def _engine_kwargs(url: str) -> dict:
    """Driver-specific engine options.

    `connect_timeout` is a libpq/psycopg connection parameter. Passing it to
    SQLite's driver raises `TypeError: 'connect_timeout' is an invalid keyword
    argument`, so it must not be sent unconditionally.

    SQLite instead needs `check_same_thread=False`: FastAPI serves requests from
    a thread pool, and SQLite's default refuses to use a connection from any
    thread other than the one that created it. SQLModel Sessions are per-request
    and never shared concurrently, so relaxing this is safe here.
    """
    if _is_sqlite(url):
        return {"connect_args": {"check_same_thread": False}}
    # pool_pre_ping avoids stale-connection errors against Supabase's pooler.
    # connect_timeout keeps startup/health checks fast-failing instead of hanging
    # on an unreachable host (matters for Render cold starts as much as local dev).
    return {"pool_pre_ping": True, "connect_args": {"connect_timeout": 5}}


engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    **_engine_kwargs(settings.DATABASE_URL),
)

USING_SQLITE = _is_sqlite(settings.DATABASE_URL)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a SQLModel Session."""
    with Session(engine) as session:
        yield session


def create_db_and_tables() -> None:
    """Create every table declared by the SQLModel metadata.

    Used for SQLite only. Against Postgres the schema is owned by Supabase
    migrations: calling this there would let the app's model definitions drift
    into being the de-facto schema authority, which is exactly the kind of
    silent divergence that makes a release decision untrustworthy.

    Importing app.models here (not at module import time) guarantees every model
    class has been registered on SQLModel.metadata before create_all runs —
    otherwise only the tables whose modules happened to be imported already get
    created, and the rest fail at first query with "no such table".
    """
    import app.models  # noqa: F401  - registers all tables on SQLModel.metadata

    SQLModel.metadata.create_all(engine)
