from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import JSON, Field, SQLModel

from app.models.enums import ResultStatus, SeverityLevel


class TestResult(SQLModel, table=True):
    __tablename__ = "test_results"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    test_run_id: uuid.UUID = Field(foreign_key="test_runs.id")
    test_case_id: uuid.UUID = Field(foreign_key="test_cases.id")
    test_case_version: int
    execution_prompt: str
    model_response: Optional[str] = None
    raw_request_payload: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    raw_response_payload: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    http_status: Optional[int] = None
    latency_ms: Optional[int] = None
    result: ResultStatus = Field(
        sa_column=Column(SAEnum(ResultStatus, name="result_status"), nullable=False)
    )
    severity: SeverityLevel = Field(
        sa_column=Column(SAEnum(SeverityLevel, name="severity_level"), nullable=False)
    )
    confidence: float = 0.0
    evidence: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    evaluator_version: str
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
