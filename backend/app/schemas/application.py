from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel

from app.models.enums import AppStatus, AppType


class ApplicationCreate(BaseModel):
    workspace_id: uuid.UUID
    name: str
    app_type: AppType
    description: Optional[str] = None
    expected_behavior: str
    forbidden_behavior: str
    endpoint_url: str
    auth_header_name: Optional[str] = None
    auth_header_value: Optional[str] = None
    request_template: dict[str, Any] = {}
    response_path: str = "$"
    timeout_seconds: int = 30
    status: AppStatus = AppStatus.DRAFT


class ApplicationUpdate(BaseModel):
    name: Optional[str] = None
    app_type: Optional[AppType] = None
    description: Optional[str] = None
    expected_behavior: Optional[str] = None
    forbidden_behavior: Optional[str] = None
    endpoint_url: Optional[str] = None
    auth_header_name: Optional[str] = None
    auth_header_value: Optional[str] = None
    request_template: Optional[dict[str, Any]] = None
    response_path: Optional[str] = None
    timeout_seconds: Optional[int] = None
    status: Optional[AppStatus] = None


class ApplicationRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    app_type: AppType
    description: Optional[str] = None
    expected_behavior: str
    forbidden_behavior: str
    endpoint_url: str
    auth_header_name: Optional[str] = None
    request_template: dict[str, Any]
    response_path: str
    timeout_seconds: int
    status: AppStatus
    last_connection_test_at: Optional[datetime] = None
    last_connection_test_ok: Optional[bool] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConnectionTestResult(BaseModel):
    ok: bool
    latency_ms: Optional[int] = None
    status_code: Optional[int] = None
    error: Optional[str] = None
    response_preview: Optional[str] = None
