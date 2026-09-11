from __future__ import annotations

import logging

from fastapi import APIRouter, Response
from sqlmodel import Session, text

from app.core.db import engine

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
def health(response: Response):
    """Liveness/readiness probe.

    Never raises: a DB outage must surface as a 503 JSON body (for Render's
    health check and for operators), not an unhandled 500 with a stack trace
    that leaks internal connection details to any caller.
    """
    try:
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as exc:  # noqa: BLE001 - deliberately broad: any DB failure -> degraded
        logger.exception("Health check DB probe failed")
        response.status_code = 503
        return {"status": "degraded", "database": "unreachable", "error_type": type(exc).__name__}
