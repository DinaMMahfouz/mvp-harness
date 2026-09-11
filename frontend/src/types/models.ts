// Mirrors backend/app/schemas/*.py — these are the frontend's TypeScript type source of truth.
import type {
  AppStatus,
  AppType,
  FindingStatus,
  NotificationChannel,
  NotificationStatus,
  NotificationTrigger,
  ReleaseDecisionEnum,
  ResultStatus,
  RunStatus,
  RunType,
  SeverityLevel,
  SuiteSource,
  TestCategory,
} from "./enums";

export interface Workspace {
  id: string;
  name: string;
  owner_email: string;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceCreate {
  name: string;
  owner_email: string;
}

export interface Application {
  id: string;
  workspace_id: string;
  name: string;
  app_type: AppType;
  description?: string | null;
  expected_behavior: string;
  forbidden_behavior: string;
  endpoint_url: string;
  auth_header_name?: string | null;
  request_template: Record<string, unknown>;
  response_path: string;
  timeout_seconds: number;
  status: AppStatus;
  last_connection_test_at?: string | null;
  last_connection_test_ok?: boolean | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationCreate {
  workspace_id: string;
  name: string;
  app_type: AppType;
  description?: string | null;
  expected_behavior: string;
  forbidden_behavior: string;
  endpoint_url: string;
  auth_header_name?: string | null;
  auth_header_value?: string | null;
  request_template: Record<string, unknown>;
  response_path: string;
  timeout_seconds: number;
  status: AppStatus;
}

export type ApplicationUpdate = Partial<ApplicationCreate>;

export interface ConnectionTestResult {
  ok: boolean;
  latency_ms?: number | null;
  status_code?: number | null;
  error?: string | null;
  response_preview?: string | null;
}

export interface TestSuite {
  id: string;
  application_id: string;
  name: string;
  description?: string | null;
  generated_at: string;
  source: SuiteSource;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TestCase {
  id: string;
  test_suite_id: string;
  category: TestCategory;
  attack_prompt: string;
  severity_if_failed: SeverityLevel;
  expected_safe_behavior: string;
  version: number;
  is_locked: boolean;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface TestCaseCreate {
  category: TestCategory;
  attack_prompt: string;
  severity_if_failed: SeverityLevel;
  expected_safe_behavior: string;
  enabled?: boolean;
}

export interface TestCaseUpdate {
  attack_prompt?: string;
  severity_if_failed?: SeverityLevel;
  expected_safe_behavior?: string;
  enabled?: boolean;
}

export interface TestRun {
  id: string;
  application_id: string;
  test_suite_id: string;
  run_type: RunType;
  triggered_by: string;
  status: RunStatus;
  started_at?: string | null;
  completed_at?: string | null;
  assurance_score?: number | null;
  created_at: string;
  updated_at: string;
}

export interface TestResult {
  id: string;
  test_run_id: string;
  test_case_id: string;
  test_case_version: number;
  execution_prompt: string;
  model_response?: string | null;
  raw_response_payload?: Record<string, unknown> | null;
  http_status?: number | null;
  latency_ms?: number | null;
  result: ResultStatus;
  severity: SeverityLevel;
  confidence: number;
  evidence: Record<string, unknown>;
  evaluator_version: string;
  evaluated_at: string;
  created_at: string;
}

export interface Finding {
  id: string;
  application_id: string;
  test_result_id: string;
  category: TestCategory;
  severity: SeverityLevel;
  title: string;
  root_cause: string;
  recommendation: string;
  status: FindingStatus;
  first_seen_run_id: string;
  last_seen_run_id: string;
  created_at: string;
  resolved_at?: string | null;
  updated_at: string;
}

export interface RemediationCreate {
  status: FindingStatus;
  note?: string | null;
  changed_by: string;
}

export interface Remediation {
  id: string;
  finding_id: string;
  status: FindingStatus;
  note?: string | null;
  changed_by: string;
  changed_at: string;
}

export interface RetestComparison {
  id: string;
  application_id: string;
  baseline_run_id: string;
  retest_run_id: string;
  fixed_count: number;
  remaining_count: number;
  regression_count: number;
  new_count: number;
  details: Array<Record<string, unknown>>;
  created_at: string;
}

export interface ReleaseDecision {
  id: string;
  application_id: string;
  test_run_id: string;
  decision: ReleaseDecisionEnum;
  blocking_findings_count: number;
  conditions: string[];
  assurance_score: number;
  rationale: string;
  decided_at: string;
}

export interface Notification {
  id: string;
  application_id: string;
  finding_id?: string | null;
  channel: NotificationChannel;
  trigger_event: NotificationTrigger;
  status: NotificationStatus;
  n8n_execution_id?: string | null;
  sent_at?: string | null;
  created_at: string;
}

export interface WebhookTriggerRequest {
  application_id: string;
  trigger_event: NotificationTrigger;
  finding_id?: string | null;
  test_run_id?: string | null;
}
