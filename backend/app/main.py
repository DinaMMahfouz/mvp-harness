from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.routers import (
    applications,
    automation,
    comparisons,
    findings,
    health,
    release_decisions,
    reports,
    runs,
    test_suites,
    workspaces,
)
from app.core.config import settings
from app.core.db import USING_SQLITE, create_db_and_tables, engine

logger = logging.getLogger("harness")

app = FastAPI(title="HARNESS — AI Release Assurance API", version="0.1.0")


@app.middleware("http")
async def catch_unhandled_exceptions(request: Request, call_next):
    """Guarantee every unhandled error is a normal, CORS-visible JSON response.

    Two real problems this fixes:
    1. Security: an uncaught exception (e.g. a DB outage) would otherwise
       leak a full internal stack trace (hosts, driver internals) to any
       caller via Starlette's default debug response.
    2. Correctness: Starlette gives @app.exception_handler(Exception) special
       treatment - it's handled by ServerErrorMiddleware, which sits OUTSIDE
       CORSMiddleware in the ASGI stack, so its responses never get CORS
       headers attached. The browser then reports a passing backend response
       as "blocked by CORS policy" / net::ERR_FAILED, and a fetch() promise
       never resolves the way calling code expects. A plain @app.middleware
       registered BEFORE add_middleware(CORSMiddleware, ...) below sits
       INSIDE CORS (last-added-is-outermost), so whatever it returns -
       including a caught exception's response - flows back out through
       CORSMiddleware and gets headers applied correctly.
    Verified live: without this, GET /api/applications during a DB outage
    produced a 500 with no CORS header, which Chrome surfaced as
    net::ERR_FAILED and left the frontend stuck on "Loading..." forever
    instead of rendering its error state.
    """
    try:
        return await call_next(request)
    except Exception as exc:  # noqa: BLE001 - deliberately broad: last line of defense
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        status_code = 503 if isinstance(exc, SQLAlchemyError) else 500
        detail = "Database unavailable" if isinstance(exc, SQLAlchemyError) else "Internal server error"
        return JSONResponse(status_code=status_code, content={"detail": detail, "error_type": type(exc).__name__})


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(workspaces.router, prefix="/api")
app.include_router(applications.router, prefix="/api")
app.include_router(test_suites.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
app.include_router(findings.router, prefix="/api")
app.include_router(comparisons.router, prefix="/api")
app.include_router(release_decisions.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(automation.router, prefix="/api")


@app.on_event("startup")
def on_startup() -> None:
    if USING_SQLITE:
        # Local SQLite has no migration pipeline: the file may not exist yet, or
        # may predate a model change. Creating tables here is idempotent
        # (create_all skips what already exists) and is what makes a fresh clone
        # runnable with no external database. Deliberately NOT done for Postgres,
        # where Supabase migrations own the schema.
        try:
            create_db_and_tables()
            logger.info("SQLite schema ensured (local development database)")
        except Exception:
            logger.exception("Failed to create SQLite schema at startup")

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(
            "Database connectivity check OK (env=%s, backend=%s)",
            settings.ENV,
            "sqlite" if USING_SQLITE else "postgres",
        )
    except Exception:
        logger.exception("Database connectivity check FAILED at startup")


@app.get("/")
def root():
    return {"service": "harness-backend", "status": "running"}
