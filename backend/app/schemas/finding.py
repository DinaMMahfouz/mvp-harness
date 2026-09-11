from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import FindingStatus, SeverityLevel, TestCategory


class FindingRead(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    test_result_id: uuid.UUID
    category: TestCategory
    severity: SeverityLevel
    title: str
    root_cause: str
    recommendation: str
    status: FindingStatus
    first_seen_run_id: uuid.UUID
    last_seen_run_id: uuid.UUID
    created_at: datetime
    resolved_at: Optional[datetime] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class RemediationCreate(BaseModel):
    status: FindingStatus
    note: Optional[str] = None
    changed_by: str


class RemediationRead(BaseModel):
    id: uuid.UUID
    finding_id: uuid.UUID
    status: FindingStatus
    note: Optional[str] = None
    changed_by: str
    changed_at: datetime

    class Config:
        from_attributes = True
