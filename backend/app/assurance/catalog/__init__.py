"""Catalog registry: maps each application type to its seed test cases.

Contract (relied on by the Backend Engineer's seeding/plan-generation logic):
each `*_cases.py` module exports a module-level list named `TEST_CASES`, where
every item is a plain dict with exactly these keys:

    category               str   one of PROMPT_INJECTION, SYSTEM_PROMPT_LEAKAGE,
                                  SCOPE_ESCAPE, HALLUCINATION_TRAP,
                                  UNSUPPORTED_CLAIMS, UNAUTHORIZED_TOOL_REQUEST,
                                  UNSAFE_PARAMETERS
    attack_prompt          str   the exact prompt/content to send
    severity_if_failed     str   one of INFO, LOW, MEDIUM, HIGH, CRITICAL
    expected_safe_behavior str   concrete description of a passing response,
                                  used by both the deterministic checks and
                                  the Claude semantic evaluator prompt

`CATALOG_BY_APP_TYPE` is the single lookup the Backend Engineer should import
from when generating a test plan for a given `applications.app_type` value.
"""

from . import (
    agent_cases,
    chatbot_cases,
    mcp_cases,
    rag_cases,
    workflow_cases,
)

CATALOG_BY_APP_TYPE: dict[str, list[dict]] = {
    "CHATBOT": chatbot_cases.TEST_CASES,
    "RAG": rag_cases.TEST_CASES,
    "AGENT": agent_cases.TEST_CASES,
    "MCP": mcp_cases.TEST_CASES,
    "WORKFLOW": workflow_cases.TEST_CASES,
}
