from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column
from sqlmodel import JSON, Field, SQLModel


class IssueExport(SQLModel, table=True):
    __tablename__ = "issue_exports"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    application_id: uuid.UUID = Field(foreign_key="applications.id")
    test_run_id: Optional[uuid.UUID] = Field(default=None, foreign_key="test_runs.id")
    file_path_or_url: str
    generated_by: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    sheet_summary: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
