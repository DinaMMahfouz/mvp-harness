"""CRUD for applications + a real connection-test that hits the registered endpoint."""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlmodel import Session, select

from app.models import Application
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ConnectionTestResult

TEST_PROMPT = "Hello, are you working?"


def _substitute(template: dict[str, Any], prompt: str) -> dict[str, Any]:
    """Recursively substitute the literal token '{{prompt}}' with `prompt`."""

    def walk(node: Any) -> Any:
        if isinstance(node, str):
            return node.replace("{{prompt}}", prompt)
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    return walk(template)


def create_application(session: Session, data: ApplicationCreate) -> Application:
    app = Application(**data.model_dump())
    session.add(app)
    session.commit()
    session.refresh(app)
    return app


def get_application(session: Session, application_id: uuid.UUID) -> Application | None:
    return session.get(Application, application_id)


def list_applications(
    session: Session,
    workspace_id: uuid.UUID | None = None,
    app_type: str | None = None,
    search: str | None = None,
) -> list[Application]:
    stmt = select(Application)
    if workspace_id is not None:
        stmt = stmt.where(Application.workspace_id == workspace_id)
    if app_type is not None:
        stmt = stmt.where(Application.app_type == app_type)
    if search:
        stmt = stmt.where(Application.name.ilike(f"%{search}%"))
    return list(session.exec(stmt))


def update_application(
    session: Session, application: Application, data: ApplicationUpdate
) -> Application:
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(application, key, value)
    application.updated_at = datetime.now(timezone.utc)
    session.add(application)
    session.commit()
    session.refresh(application)
    return application


def delete_application(session: Session, application: Application) -> None:
    session.delete(application)
    session.commit()


def test_connection(session: Session, application: Application) -> ConnectionTestResult:
    """Fire a real HTTP POST at application.endpoint_url with a harmless prompt."""
    payload = _substitute(application.request_template, TEST_PROMPT)
    headers = {}
    if application.auth_header_name and application.auth_header_value:
        headers[application.auth_header_name] = application.auth_header_value

    start = time.monotonic()
    result: ConnectionTestResult
    try:
        with httpx.Client(timeout=application.timeout_seconds) as client:
            response = client.post(application.endpoint_url, json=payload, headers=headers)
        latency_ms = int((time.monotonic() - start) * 1000)
        ok = 200 <= response.status_code < 300
        result = ConnectionTestResult(
            ok=ok,
            latency_ms=latency_ms,
            status_code=response.status_code,
            response_preview=response.text[:500],
        )
    except httpx.HTTPError as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        result = ConnectionTestResult(ok=False, latency_ms=latency_ms, error=str(exc))

    application.last_connection_test_at = datetime.now(timezone.utc)
    application.last_connection_test_ok = result.ok
    session.add(application)
    session.commit()
    return result
