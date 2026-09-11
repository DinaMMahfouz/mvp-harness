from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import NotificationChannel, NotificationStatus, NotificationTrigger


class NotificationRead(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    finding_id: Optional[uuid.UUID] = None
    channel: NotificationChannel
    trigger_event: NotificationTrigger
    status: NotificationStatus
    n8n_execution_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookTriggerRequest(BaseModel):
    application_id: uuid.UUID
    trigger_event: NotificationTrigger
    finding_id: Optional[uuid.UUID] = None
    test_run_id: Optional[uuid.UUID] = None


class AutomationCallbackPayload(BaseModel):
    event_id: uuid.UUID
    notification_id: uuid.UUID
    status: NotificationStatus
    n8n_execution_id: Optional[str] = None
    error_message: Optional[str] = None
