"""Shared FastAPI dependencies: DB session + a minimal auth stub.

V2 gap (documented, not a silent omission): real auth (Supabase JWT / OAuth)
is out of scope for this MVP. `get_current_user` reads an `X-User-Email`
header if present and falls back to "anonymous" — enough to attribute
`triggered_by` / `changed_by` fields without blocking the demo. Replace with
real JWT verification before any production use beyond the MVP demo.
"""
from __future__ import annotations

from typing import Iterator

from fastapi import Header
from sqlmodel import Session

from app.core.db import get_session as _get_session

get_session = _get_session


def get_current_user(x_user_email: str | None = Header(default=None)) -> str:
    return x_user_email or "anonymous"
