import type {
  Application,
  ApplicationCreate,
  ApplicationUpdate,
  ConnectionTestResult,
  Finding,
  Notification,
  ReleaseDecision,
  Remediation,
  RemediationCreate,
  RetestComparison,
  TestCase,
  TestCaseCreate,
  TestCaseUpdate,
  TestResult,
  TestRun,
  TestSuite,
  WebhookTriggerRequest,
  Workspace,
  WorkspaceCreate,
} from "../types/models";
import type { AppType, FindingStatus, NotificationTrigger } from "../types/enums";

const BASE_URL: string = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, message: string, body?: unknown) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers || {}),
      },
    });
  } catch (err) {
    throw new ApiError(0, `Network error reaching HARNESS API at ${BASE_URL}${path}. Is the backend running?`);
  }

  if (!res.ok) {
    let body: unknown = undefined;
    let message = `Request failed (${res.status})`;
    try {
      body = await res.json();
      if (body && typeof body === "object" && "detail" in body) {
        message = String((body as { detail: unknown }).detail);
      }
    } catch {
      // no JSON body
    }
    throw new ApiError(res.status, message, body);
  }

  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

function qs(params: Record<string, string | undefined | null>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "");
  if (entries.length === 0) return "";
  return "?" + entries.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v as string)}`).join("&");
}

export const api = {
  // Workspaces
  listWorkspaces: () => request<Workspace[]>("/workspaces"),
  createWorkspace: (data: WorkspaceCreate) =>
    request<Workspace>("/workspaces", { method: "POST", body: JSON.stringify(data) }),

  // Applications
  listApplications: (params?: { workspace_id?: string; app_type?: AppType; search?: string }) =>
    request<Application[]>(`/applications${qs(params || {})}`),
  getApplication: (id: string) => request<Application>(`/applications/${id}`),
  createApplication: (data: ApplicationCreate) =>
    request<Application>("/applications", { method: "POST", body: JSON.stringify(data) }),
  updateApplication: (id: string, data: ApplicationUpdate) =>
    request<Application>(`/applications/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteApplication: (id: string) => request<void>(`/applications/${id}`, { method: "DELETE" }),
  testConnection: (id: string) =>
    request<ConnectionTestResult>(`/applications/${id}/test-connection`, { method: "POST" }),

  // Test plan / suites / cases
  generateTestPlan: (applicationId: string, name?: string, description?: string) =>
    request<TestSuite>(`/applications/${applicationId}/test-plan/generate`, {
      method: "POST",
      body: JSON.stringify({ name, description }),
    }),
  listTestSuites: (applicationId: string) =>
    request<TestSuite[]>(`/applications/${applicationId}/test-suites`),
  getTestSuite: (id: string) => request<TestSuite>(`/test-suites/${id}`),
  listTestCases: (testSuiteId: string) => request<TestCase[]>(`/test-suites/${testSuiteId}/test-cases`),
  addTestCase: (testSuiteId: string, data: TestCaseCreate) =>
    request<TestCase>(`/test-suites/${testSuiteId}/test-cases`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  editTestCase: (testCaseId: string, data: TestCaseUpdate) =>
    request<TestCase>(`/test-cases/${testCaseId}`, { method: "PATCH", body: JSON.stringify(data) }),

  // Runs
  executeRun: (applicationId: string, testSuiteId: string, triggeredBy = "manual") =>
    request<TestRun>(`/applications/${applicationId}/runs`, {
      method: "POST",
      body: JSON.stringify({ test_suite_id: testSuiteId, triggered_by: triggeredBy }),
    }),
  listRuns: (applicationId: string) => request<TestRun[]>(`/applications/${applicationId}/runs`),
  getRun: (id: string) => request<TestRun>(`/runs/${id}`),
  getRunResults: (id: string) => request<TestResult[]>(`/runs/${id}/results`),
  retest: (applicationId: string, basedOnRunId: string, scope: "failed_only" | "full_suite", triggeredBy = "manual") =>
    request<TestRun>(`/applications/${applicationId}/retest`, {
      method: "POST",
      body: JSON.stringify({ based_on_run_id: basedOnRunId, scope, triggered_by: triggeredBy }),
    }),

  // Findings
  listFindings: (applicationId: string, status?: FindingStatus) =>
    request<Finding[]>(`/applications/${applicationId}/findings${qs({ status })}`),
  getFinding: (id: string) => request<Finding>(`/findings/${id}`),
  listRemediations: (findingId: string) => request<Remediation[]>(`/findings/${findingId}/remediations`),
  updateFindingStatus: (findingId: string, data: RemediationCreate) =>
    request<Finding>(`/findings/${findingId}/remediation`, { method: "PATCH", body: JSON.stringify(data) }),

  // Comparisons
  createComparison: (baselineRunId: string, retestRunId: string) =>
    request<RetestComparison>(
      `/comparisons?baseline_run_id=${encodeURIComponent(baselineRunId)}&retest_run_id=${encodeURIComponent(retestRunId)}`,
      { method: "POST" }
    ),
  listComparisons: (applicationId: string) =>
    request<RetestComparison[]>(`/applications/${applicationId}/comparisons`),
  getComparison: (id: string) => request<RetestComparison>(`/comparisons/${id}`),

  // Release decisions
  recomputeReleaseDecision: (runId: string) =>
    request<ReleaseDecision>(`/runs/${runId}/release-decision/recompute`, { method: "POST" }),
  getLatestReleaseDecisionForRun: (runId: string) =>
    request<ReleaseDecision>(`/runs/${runId}/release-decision`),
  listReleaseDecisions: (applicationId: string) =>
    request<ReleaseDecision[]>(`/applications/${applicationId}/release-decisions`),

  // Automation
  triggerWebhook: (data: WebhookTriggerRequest) =>
    request<Notification>("/automation/webhook-trigger", { method: "POST", body: JSON.stringify(data) }),

  // Reports — Excel export (blob download, not JSON)
  exportExcel: async (applicationId: string, applicationName: string): Promise<void> => {
    const res = await fetch(`${BASE_URL}/applications/${applicationId}/reports/export/excel`, {
      method: "POST",
    });
    if (!res.ok) {
      let message = `Export failed (${res.status})`;
      try {
        const body = await res.json();
        if (body && typeof body === "object" && "detail" in body) {
          message = String((body as { detail: unknown }).detail);
        }
      } catch {
        // ignore
      }
      throw new ApiError(res.status, message);
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `harness_issue_register_${applicationName.replace(/\s+/g, "_")}.xlsx`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },
};

export type { NotificationTrigger };
