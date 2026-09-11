from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.models.enums import NotificationChannel, NotificationStatus, NotificationTrigger


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    application_id: uuid.UUID = Field(foreign_key="applications.id")
    finding_id: Optional[uuid.UUID] = Field(default=None, foreign_key="findings.id")
    channel: NotificationChannel = Field(
        default=NotificationChannel.EMAIL,
        sa_column=Column(SAEnum(NotificationChannel, name="notification_channel"), nullable=False),
    )
    trigger_event: NotificationTrigger = Field(
        sa_column=Column(SAEnum(NotificationTrigger, name="notification_trigger"), nullable=False)
    )
    status: NotificationStatus = Field(
        default=NotificationStatus.PENDING,
        sa_column=Column(SAEnum(NotificationStatus, name="notification_status"), nullable=False),
    )
    n8n_execution_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
