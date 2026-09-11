"""Verify the signature on an inbound n8n callback before trusting its body."""
from __future__ import annotations

from app.core.config import settings
from app.core.security import verify_signature


def verify_callback(body: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    return verify_signature(settings.HARNESS_WEBHOOK_SECRET, body, signature)
