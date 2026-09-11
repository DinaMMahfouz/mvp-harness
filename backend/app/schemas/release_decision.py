from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ReleaseDecisionEnum


class ReleaseDecisionRead(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    test_run_id: uuid.UUID
    decision: ReleaseDecisionEnum
    blocking_findings_count: int
    conditions: list[str]
    assurance_score: float
    rationale: str
    decided_at: datetime

    class Config:
        from_attributes = True
