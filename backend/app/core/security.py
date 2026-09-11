"""HMAC signing/verification for the n8n webhook contract.

n8n signs outgoing callbacks with HARNESS_WEBHOOK_SECRET; we verify them here.
We also sign outbound webhook-trigger payloads the same way so n8n can verify
they actually came from HARNESS.
"""
from __future__ import annotations

import hashlib
import hmac


def sign_payload(secret: str, body: bytes) -> str:
    """Return the hex-encoded HMAC-SHA256 digest of `body` using `secret`."""
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def verify_signature(secret: str, body: bytes, signature: str) -> bool:
    """Constant-time comparison of a provided signature against the expected one."""
    if not signature:
        return False
    expected = sign_payload(secret, body)
    return hmac.compare_digest(expected, signature)
