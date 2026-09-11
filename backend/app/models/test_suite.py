from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.models.enums import SuiteSource


class TestSuite(SQLModel, table=True):
    __tablename__ = "test_suites"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    application_id: uuid.UUID = Field(foreign_key="applications.id")
    name: str
    description: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    source: SuiteSource = Field(
        default=SuiteSource.SEEDED,
        sa_column=Column(SAEnum(SuiteSource, name="suite_source"), nullable=False),
    )
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
