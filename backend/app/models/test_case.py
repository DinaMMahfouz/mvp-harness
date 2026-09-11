from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import JSON, Field, SQLModel

from app.models.enums import SeverityLevel, TestCategory


class TestCase(SQLModel, table=True):
    __tablename__ = "test_cases"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    test_suite_id: uuid.UUID = Field(foreign_key="test_suites.id")
    category: TestCategory = Field(
        sa_column=Column(SAEnum(TestCategory, name="test_category"), nullable=False)
    )
    attack_prompt: str
    severity_if_failed: SeverityLevel = Field(
        sa_column=Column(SAEnum(SeverityLevel, name="severity_level"), nullable=False)
    )
    expected_safe_behavior: str
    version: int = 1
    is_locked: bool = False
    applicable_app_types: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
