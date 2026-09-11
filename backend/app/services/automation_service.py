"""Build/send the n8n webhook-trigger payload and handle signed callbacks.

HARNESS's job here is strictly: build the payload, sign it, send it, record
a notification row, and process the signed callback that updates that row's
status — never compute severity/score/release logic (that stays in
scoring_service / finding_service, owned by this codebase, not n8n).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlmodel import Session

from app.automation.callback_verifier import verify_callback
from app.automation.webhook_client import WebhookDeliveryError, send_webhook
from app.models import (
    Application,
    AutomationError,
    AutomationEvent,
    AutomationType,
    Finding,
    Notification,
    NotificationStatus,
    NotificationTrigger,
)


def build_webhook_payload(
    application: Application,
    trigger_event: NotificationTrigger,
    notification_id: uuid.UUID,
    finding: Finding | None = None,
    test_run_id: uuid.UUID | None = None,
) -> dict:
    payload = {
        "notification_id": str(notification_id),
        "trigger_event": trigger_event.value,
        "application": {
            "id": str(application.id),
            "name": application.name,
            "app_type": application.app_type.value,
        },
        "test_run_id": str(test_run_id) if test_run_id else None,
    }
    if finding is not None:
        payload["finding"] = {
            "id": str(finding.id),
            "category": finding.category.value,
            "severity": finding.severity.value,
            "title": finding.title,
            "root_cause": finding.root_cause,
            "recommendation": finding.recommendation,
        }
    return payload


def trigger_webhook(
    session: Session,
    application: Application,
    trigger_event: NotificationTrigger,
    finding: Finding | None = None,
    test_run_id: uuid.UUID | None = None,
) -> Notification:
    notification = Notification(
        application_id=application.id,
        finding_id=finding.id if finding else None,
        trigger_event=trigger_event,
        status=NotificationStatus.PENDING,
    )
    session.add(notification)
    session.commit()
    session.refresh(notification)

    payload = build_webhook_payload(application, trigger_event, notification.id, finding, test_run_id)

    try:
        response = send_webhook(payload)
        if 200 <= response.status_code < 300:
            # Actual SENT confirmation comes from the signed callback; a 2xx
            # here only confirms n8n accepted the trigger.
            pass
        else:
            _record_error(
                session,
                AutomationType.WEBHOOK_TRIGGER,
                application.id,
                notification.id,
                f"n8n webhook returned HTTP {response.status_code}: {response.text[:500]}",
                payload,
            )
            notification.status = NotificationStatus.FAILED
            session.add(notification)
            session.commit()
    except WebhookDeliveryError as exc:
        _record_error(
            session, AutomationType.WEBHOOK_TRIGGER, application.id, notification.id, str(exc), payload
        )
        notification.status = NotificationStatus.FAILED
        session.add(notification)
        session.commit()

    session.refresh(notification)
    return notification


def _record_error(
    session: Session,
    automation_type: AutomationType,
    application_id: uuid.UUID | None,
    notification_id: uuid.UUID | None,
    error_message: str,
    payload_snapshot: dict | None,
) -> AutomationError:
    error = AutomationError(
        automation_type=automation_type,
        application_id=application_id,
        notification_id=notification_id,
        error_message=error_message,
        payload_snapshot=payload_snapshot,
    )
    session.add(error)
    session.commit()
    session.refresh(error)
    return error


class InvalidCallbackSignatureError(ValueError):
    pass


def handle_callback(
    session: Session,
    body: bytes,
    signature: str | None,
    event_id: uuid.UUID,
    notification_id: uuid.UUID,
    status: NotificationStatus,
    n8n_execution_id: str | None = None,
    error_message: str | None = None,
) -> Notification | None:
    """Verify signature, apply duplicate-event protection, update the notification.

    Returns None (no-op) for a duplicate event_id already recorded in
    automation_events, per the plan's "duplicate-event protection" requirement.
    """
    if not verify_callback(body, signature):
        raise InvalidCallbackSignatureError("Invalid or missing X-Harness-Signature header")

    existing_event = session.get(AutomationEvent, event_id)
    if existing_event is not None:
        return None  # already processed — idempotent no-op

    session.add(AutomationEvent(event_id=event_id))
    session.commit()

    notification = session.get(Notification, notification_id)
    if notification is None:
        _record_error(
            session,
            AutomationType.CALLBACK,
            None,
            None,
            f"Callback referenced unknown notification_id={notification_id}",
            {"event_id": str(event_id)},
        )
        return None

    notification.status = status
    notification.n8n_execution_id = n8n_execution_id
    if status == NotificationStatus.SENT:
        notification.sent_at = datetime.now(timezone.utc)
    session.add(notification)
    session.commit()

    if status == NotificationStatus.FAILED:
        _record_error(
            session,
            AutomationType.CALLBACK,
            notification.application_id,
            notification.id,
            error_message or "n8n reported callback status=FAILED",
            None,
        )

    session.refresh(notification)
    return notification
