from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import SuiteSource


class TestSuiteRead(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    name: str
    description: Optional[str] = None
    generated_at: datetime
    source: SuiteSource
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GeneratePlanRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
