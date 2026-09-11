from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.models.enums import FindingStatus


class Remediation(SQLModel, table=True):
    """Append-only status-transition history for a finding.

    findings.status always mirrors the most recent remediation row for that
    finding_id — never write to findings.status without inserting one of these.
    """

    __tablename__ = "remediations"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    finding_id: uuid.UUID = Field(foreign_key="findings.id")
    status: FindingStatus = Field(
        sa_column=Column(SAEnum(FindingStatus, name="finding_status"), nullable=False)
    )
    note: Optional[str] = None
    changed_by: str
    changed_at: datetime = Field(default_factory=datetime.utcnow)
