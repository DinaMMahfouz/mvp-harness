from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RetestComparisonRead(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    baseline_run_id: uuid.UUID
    retest_run_id: uuid.UUID
    fixed_count: int
    remaining_count: int
    regression_count: int
    new_count: int
    details: list[dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True
