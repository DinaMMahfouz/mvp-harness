from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import JSON, Field, SQLModel

from app.models.enums import AutomationType


class AutomationError(SQLModel, table=True):
    __tablename__ = "automation_errors"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    automation_type: AutomationType = Field(
        sa_column=Column(SAEnum(AutomationType, name="automation_type"), nullable=False)
    )
    application_id: Optional[uuid.UUID] = Field(default=None, foreign_key="applications.id")
    notification_id: Optional[uuid.UUID] = Field(default=None, foreign_key="notifications.id")
    error_message: str
    payload_snapshot: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
