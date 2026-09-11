from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import SeverityLevel, TestCategory


class TestCaseRead(BaseModel):
    id: uuid.UUID
    test_suite_id: uuid.UUID
    category: TestCategory
    attack_prompt: str
    severity_if_failed: SeverityLevel
    expected_safe_behavior: str
    version: int
    is_locked: bool
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestCaseUpdate(BaseModel):
    """Editing a locked case creates a new version row instead of mutating it."""

    attack_prompt: Optional[str] = None
    severity_if_failed: Optional[SeverityLevel] = None
    expected_safe_behavior: Optional[str] = None
    enabled: Optional[bool] = None


class TestCaseCreate(BaseModel):
    category: TestCategory
    attack_prompt: str
    severity_if_failed: SeverityLevel
    expected_safe_behavior: str
    enabled: bool = True
