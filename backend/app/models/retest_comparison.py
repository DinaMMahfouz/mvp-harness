from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column
from sqlmodel import JSON, Field, SQLModel


class RetestComparison(SQLModel, table=True):
    __tablename__ = "retest_comparisons"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    application_id: uuid.UUID = Field(foreign_key="applications.id")
    baseline_run_id: uuid.UUID = Field(foreign_key="test_runs.id")
    retest_run_id: uuid.UUID = Field(foreign_key="test_runs.id")
    fixed_count: int = 0
    remaining_count: int = 0
    regression_count: int = 0
    new_count: int = 0
    # list[{"test_case_id": str, "classification": "FIXED"|"REMAINING"|"REGRESSION"|"NEW", ...}]
    details: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
