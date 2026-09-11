"""Python enums mirroring the Postgres enum types already applied to Supabase.

Names and members here must match the DB enum labels exactly (verified live
against the Supabase project via `list_tables`/`execute_sql` on
pg_enum) — do not rename members without a matching DB migration.
"""
from __future__ import annotations

import enum


class AppType(str, enum.Enum):
    CHATBOT = "CHATBOT"
    RAG = "RAG"
    AGENT = "AGENT"
    MCP = "MCP"
    WORKFLOW = "WORKFLOW"


class AppStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class SuiteSource(str, enum.Enum):
    SEEDED = "SEEDED"
    CUSTOM = "CUSTOM"
    MIXED = "MIXED"


class TestCategory(str, enum.Enum):
    PROMPT_INJECTION = "PROMPT_INJECTION"
    SYSTEM_PROMPT_LEAKAGE = "SYSTEM_PROMPT_LEAKAGE"
    SCOPE_ESCAPE = "SCOPE_ESCAPE"
    HALLUCINATION_TRAP = "HALLUCINATION_TRAP"
    UNSUPPORTED_CLAIMS = "UNSUPPORTED_CLAIMS"
    UNAUTHORIZED_TOOL_REQUEST = "UNAUTHORIZED_TOOL_REQUEST"
    UNSAFE_PARAMETERS = "UNSAFE_PARAMETERS"


class SeverityLevel(str, enum.Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RunType(str, enum.Enum):
    BASELINE = "BASELINE"
    RETEST = "RETEST"


class RunStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ResultStatus(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"
    ERROR = "ERROR"


class FindingStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    ACCEPT_RISK = "ACCEPT_RISK"


class ReleaseDecisionEnum(str, enum.Enum):
    READY = "READY"
    READY_WITH_CONDITIONS = "READY_WITH_CONDITIONS"
    NOT_READY = "NOT_READY"


class NotificationChannel(str, enum.Enum):
    EMAIL = "EMAIL"


class NotificationTrigger(str, enum.Enum):
    CRITICAL_FOUND = "CRITICAL_FOUND"
    RUN_COMPLETED = "RUN_COMPLETED"
    RELEASE_DECISION_MADE = "RELEASE_DECISION_MADE"


class NotificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class AutomationType(str, enum.Enum):
    WEBHOOK_TRIGGER = "WEBHOOK_TRIGGER"
    CALLBACK = "CALLBACK"
