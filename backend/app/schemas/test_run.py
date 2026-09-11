from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import RunStatus, RunType


class TestRunRead(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    test_suite_id: uuid.UUID
    run_type: RunType
    triggered_by: str
    status: RunStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assurance_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExecuteRunRequest(BaseModel):
    test_suite_id: uuid.UUID
    triggered_by: str = "manual"


class RetestRequest(BaseModel):
    based_on_run_id: uuid.UUID
    scope: str = "failed_only"  # "failed_only" | "full_suite"
    triggered_by: str = "manual"
