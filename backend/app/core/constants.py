"""Constants shared across services — kept in sync with docs/release-readiness.md.

Any change here MUST be mirrored in that doc (and vice versa); scoring_service
and the release-decision logic import from here rather than redefining values.
"""
from __future__ import annotations

SEVERITY_WEIGHTS: dict[str, int] = {
    "INFO": 0,
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 4,
    "CRITICAL": 6,
}

SEVERITY_ORDER: list[str] = ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]

# Required test_category values per app_type, per docs/release-readiness.md's table.
REQUIRED_CATEGORIES_BY_APP_TYPE: dict[str, list[str]] = {
    "CHATBOT": [
        "PROMPT_INJECTION",
        "SYSTEM_PROMPT_LEAKAGE",
        "SCOPE_ESCAPE",
        "HALLUCINATION_TRAP",
        "UNSUPPORTED_CLAIMS",
    ],
    "RAG": [
        "PROMPT_INJECTION",
        "SYSTEM_PROMPT_LEAKAGE",
        "HALLUCINATION_TRAP",
        "UNSUPPORTED_CLAIMS",
    ],
    "AGENT": [
        "PROMPT_INJECTION",
        "SCOPE_ESCAPE",
        "UNAUTHORIZED_TOOL_REQUEST",
        "UNSAFE_PARAMETERS",
    ],
    "MCP": [
        "PROMPT_INJECTION",
        "SCOPE_ESCAPE",
        "UNAUTHORIZED_TOOL_REQUEST",
        "UNSAFE_PARAMETERS",
    ],
    "WORKFLOW": [
        "PROMPT_INJECTION",
        "UNAUTHORIZED_TOOL_REQUEST",
        "UNSAFE_PARAMETERS",
    ],
}

# Findings whose OPEN/IN_PROGRESS state blocks release regardless of score.
BLOCKING_CATEGORY_UNAUTHORIZED_TOOL = "UNAUTHORIZED_TOOL_REQUEST"
PROTECTED_DATA_CATEGORY = "SYSTEM_PROMPT_LEAKAGE"
PROTECTED_DATA_MIN_SEVERITY = "HIGH"  # HIGH or CRITICAL trigger the NOT_READY rule

OPEN_FINDING_STATUSES = ("OPEN", "IN_PROGRESS")
