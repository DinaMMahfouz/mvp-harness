from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class WorkspaceCreate(BaseModel):
    name: str
    owner_email: str


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    owner_email: str | None = None


class WorkspaceRead(BaseModel):
    id: uuid.UUID
    name: str
    owner_email: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
