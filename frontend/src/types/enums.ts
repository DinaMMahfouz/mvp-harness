// Mirrors backend/app/models/enums.py — string values must match exactly.

export type AppType = "CHATBOT" | "RAG" | "AGENT" | "MCP" | "WORKFLOW";
export const APP_TYPES: AppType[] = ["CHATBOT", "RAG", "AGENT", "MCP", "WORKFLOW"];

export type AppStatus = "DRAFT" | "ACTIVE" | "ARCHIVED";
export const APP_STATUSES: AppStatus[] = ["DRAFT", "ACTIVE", "ARCHIVED"];

export type SuiteSource = "SEEDED" | "CUSTOM" | "MIXED";

export type TestCategory =
  | "PROMPT_INJECTION"
  | "SYSTEM_PROMPT_LEAKAGE"
  | "SCOPE_ESCAPE"
  | "HALLUCINATION_TRAP"
  | "UNSUPPORTED_CLAIMS"
  | "UNAUTHORIZED_TOOL_REQUEST"
  | "UNSAFE_PARAMETERS";

export const TEST_CATEGORIES: TestCategory[] = [
  "PROMPT_INJECTION",
  "SYSTEM_PROMPT_LEAKAGE",
  "SCOPE_ESCAPE",
  "HALLUCINATION_TRAP",
  "UNSUPPORTED_CLAIMS",
  "UNAUTHORIZED_TOOL_REQUEST",
  "UNSAFE_PARAMETERS",
];

// Product-facing grouping (per build plan): 3 categories -> Security / Reliability / Control.
export type CategoryGroup = "Security" | "Reliability" | "Control";

export const CATEGORY_GROUP: Record<TestCategory, CategoryGroup> = {
  PROMPT_INJECTION: "Security",
  SYSTEM_PROMPT_LEAKAGE: "Security",
  SCOPE_ESCAPE: "Security",
  HALLUCINATION_TRAP: "Reliability",
  UNSUPPORTED_CLAIMS: "Reliability",
  UNAUTHORIZED_TOOL_REQUEST: "Control",
  UNSAFE_PARAMETERS: "Control",
};

export type SeverityLevel = "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export const SEVERITY_LEVELS: SeverityLevel[] = ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"];
export const SEVERITY_WEIGHT: Record<SeverityLevel, number> = {
  INFO: 0,
  LOW: 1,
  MEDIUM: 2,
  HIGH: 4,
  CRITICAL: 6,
};

export type RunType = "BASELINE" | "RETEST";

export type RunStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";

export type ResultStatus = "PASS" | "FAIL" | "REVIEW" | "ERROR";
export const RESULT_STATUSES: ResultStatus[] = ["PASS", "FAIL", "REVIEW", "ERROR"];

export type FindingStatus = "OPEN" | "IN_PROGRESS" | "RESOLVED" | "ACCEPT_RISK";
export const FINDING_STATUSES: FindingStatus[] = ["OPEN", "IN_PROGRESS", "RESOLVED", "ACCEPT_RISK"];

export type ReleaseDecisionEnum = "READY" | "READY_WITH_CONDITIONS" | "NOT_READY";

export type NotificationChannel = "EMAIL";
export type NotificationTrigger = "CRITICAL_FOUND" | "RUN_COMPLETED" | "RELEASE_DECISION_MADE";
export type NotificationStatus = "PENDING" | "SENT" | "FAILED";
