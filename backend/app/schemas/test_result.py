from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel

from app.models.enums import ResultStatus, SeverityLevel


class TestResultRead(BaseModel):
    id: uuid.UUID
    test_run_id: uuid.UUID
    test_case_id: uuid.UUID
    test_case_version: int
    execution_prompt: str
    model_response: Optional[str] = None
    raw_response_payload: Optional[dict[str, Any]] = None
    http_status: Optional[int] = None
    latency_ms: Optional[int] = None
    result: ResultStatus
    severity: SeverityLevel
    confidence: float
    evidence: dict[str, Any]
    evaluator_version: str
    evaluated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
