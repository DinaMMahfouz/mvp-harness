from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.models.enums import RunStatus, RunType


class TestRun(SQLModel, table=True):
    __tablename__ = "test_runs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    application_id: uuid.UUID = Field(foreign_key="applications.id")
    test_suite_id: uuid.UUID = Field(foreign_key="test_suites.id")
    run_type: RunType = Field(
        default=RunType.BASELINE,
        sa_column=Column(SAEnum(RunType, name="run_type"), nullable=False),
    )
    triggered_by: str
    status: RunStatus = Field(
        default=RunStatus.PENDING,
        sa_column=Column(SAEnum(RunStatus, name="run_status"), nullable=False),
    )
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assurance_score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
