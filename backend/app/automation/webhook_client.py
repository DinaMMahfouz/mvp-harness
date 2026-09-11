"""Thin, signed HTTP client for triggering the n8n webhook workflow.

HARNESS only builds and signs the payload — n8n owns branching, Gmail
sending, and Excel-fetch callback logic. Never compute severity/score here.
"""
from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import settings
from app.core.security import sign_payload

WEBHOOK_TIMEOUT_SECONDS = 15


class WebhookDeliveryError(RuntimeError):
    pass


def send_webhook(payload: dict[str, Any]) -> httpx.Response:
    if not settings.N8N_WEBHOOK_URL:
        raise WebhookDeliveryError("N8N_WEBHOOK_URL is not configured")

    body = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    signature = sign_payload(settings.HARNESS_WEBHOOK_SECRET, body)

    headers = {
        "Content-Type": "application/json",
        "X-Harness-Signature": signature,
    }
    try:
        with httpx.Client(timeout=WEBHOOK_TIMEOUT_SECONDS) as client:
            response = client.post(settings.N8N_WEBHOOK_URL, content=body, headers=headers)
        return response
    except httpx.HTTPError as exc:
        raise WebhookDeliveryError(str(exc)) from exc
