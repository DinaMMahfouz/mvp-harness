from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import JSON, Field, SQLModel

from app.models.enums import AppStatus, AppType


class Application(SQLModel, table=True):
    __tablename__ = "applications"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspaces.id")
    name: str
    app_type: AppType = Field(sa_column=Column(SAEnum(AppType, name="app_type"), nullable=False))
    description: Optional[str] = None
    expected_behavior: str
    forbidden_behavior: str
    endpoint_url: str
    auth_header_name: Optional[str] = None
    auth_header_value: Optional[str] = None
    request_template: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    response_path: str = "$"
    timeout_seconds: int = 30
    status: AppStatus = Field(
        default=AppStatus.DRAFT,
        sa_column=Column(SAEnum(AppStatus, name="app_status"), nullable=False),
    )
    last_connection_test_at: Optional[datetime] = None
    last_connection_test_ok: Optional[bool] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
