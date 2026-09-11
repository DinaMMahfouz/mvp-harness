from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import JSON, Field, SQLModel

from app.models.enums import ReleaseDecisionEnum


class ReleaseDecision(SQLModel, table=True):
    __tablename__ = "release_decisions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    application_id: uuid.UUID = Field(foreign_key="applications.id")
    test_run_id: uuid.UUID = Field(foreign_key="test_runs.id")
    decision: ReleaseDecisionEnum = Field(
        sa_column=Column(SAEnum(ReleaseDecisionEnum, name="release_decision_enum"), nullable=False)
    )
    blocking_findings_count: int = 0
    conditions: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    assurance_score: float
    rationale: str
    decided_at: datetime = Field(default_factory=datetime.utcnow)
