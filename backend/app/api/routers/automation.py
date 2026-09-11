from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlmodel import Session

from app.api.deps import get_session
from app.models import Application, Finding
from app.schemas.notification import NotificationRead, WebhookTriggerRequest
from app.services import automation_service

router = APIRouter(prefix="/automation", tags=["automation"])


@router.post("/webhook-trigger", response_model=NotificationRead, status_code=201)
def webhook_trigger(data: WebhookTriggerRequest, session: Session = Depends(get_session)):
    application = session.get(Application, data.application_id)
    if application is None:
        raise HTTPException(404, "Application not found")
    finding = session.get(Finding, data.finding_id) if data.finding_id else None
    return automation_service.trigger_webhook(
        session, application, data.trigger_event, finding, data.test_run_id
    )


@router.post("/callback", status_code=200)
async def automation_callback(
    request: Request,
    session: Session = Depends(get_session),
    x_harness_signature: str | None = Header(default=None),
):
    body = await request.body()
    payload = await request.json()

    try:
        event_id = uuid.UUID(str(payload["event_id"]))
        notification_id = uuid.UUID(str(payload["notification_id"]))
    except (KeyError, ValueError) as exc:
        raise HTTPException(400, f"Malformed callback payload: {exc}") from exc

    try:
        notification = automation_service.handle_callback(
            session,
            body,
            x_harness_signature,
            event_id,
            notification_id,
            payload.get("status", "FAILED"),
            payload.get("n8n_execution_id"),
            payload.get("error_message"),
        )
    except automation_service.InvalidCallbackSignatureError as exc:
        raise HTTPException(401, str(exc)) from exc

    if notification is None:
        return {"status": "duplicate_event_ignored"}
    return {"status": "ok", "notification_id": str(notification.id)}
