from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.models.enums import FindingStatus, SeverityLevel, TestCategory


class Finding(SQLModel, table=True):
    __tablename__ = "findings"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    application_id: uuid.UUID = Field(foreign_key="applications.id")
    test_result_id: uuid.UUID = Field(foreign_key="test_results.id")
    category: TestCategory = Field(
        sa_column=Column(SAEnum(TestCategory, name="test_category"), nullable=False)
    )
    severity: SeverityLevel = Field(
        sa_column=Column(SAEnum(SeverityLevel, name="severity_level"), nullable=False)
    )
    title: str
    root_cause: str
    recommendation: str
    status: FindingStatus = Field(
        default=FindingStatus.OPEN,
        sa_column=Column(SAEnum(FindingStatus, name="finding_status"), nullable=False),
    )
    first_seen_run_id: uuid.UUID = Field(foreign_key="test_runs.id")
    last_seen_run_id: uuid.UUID = Field(foreign_key="test_runs.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
