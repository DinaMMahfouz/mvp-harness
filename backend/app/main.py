from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import text

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
from app.core.db import engine

logger = logging.getLogger("harness")

app = FastAPI(title="HARNESS — AI Release Assurance API", version="0.1.0")

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
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connectivity check OK (env=%s)", settings.ENV)
    except Exception:
        logger.exception("Database connectivity check FAILED at startup")


@app.get("/")
def root():
    return {"service": "harness-backend", "status": "running"}
