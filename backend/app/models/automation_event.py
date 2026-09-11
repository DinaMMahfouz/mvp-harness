from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class AutomationEvent(SQLModel, table=True):
    """Idempotency ledger for inbound n8n callbacks — one row per event_id.

    handle_callback() must check this table first and no-op on a duplicate
    event_id, per the plan's "duplicate-event protection" requirement.
    """

    __tablename__ = "automation_events"

    event_id: uuid.UUID = Field(primary_key=True)
    processed_at: datetime = Field(default_factory=datetime.utcnow)
