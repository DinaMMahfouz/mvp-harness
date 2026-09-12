import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import { useApi } from "../lib/useApi";
import { Loading, ErrorState } from "../components/States";
import { AuthorizedUseNotice } from "../components/AuthorizedUseNotice";
import { APP_STATUSES, APP_TYPES, type AppStatus, type AppType } from "../types/enums";
import type { ConnectionTestResult } from "../types/models";

interface FormState {
  workspace_id: string;
  name: string;
  app_type: AppType;
  description: string;
  expected_behavior: string;
  forbidden_behavior: string;
  endpoint_url: string;
  auth_header_name: string;
  auth_header_value: string;
  request_template: string; // raw JSON text while editing
  response_path: string;
  timeout_seconds: number;
  status: AppStatus;
}

const EMPTY_FORM: FormState = {
  workspace_id: "",
  name: "",
  app_type: "CHATBOT",
  description: "",
  expected_behavior: "",
  forbidden_behavior: "",
  endpoint_url: "",
  auth_header_name: "",
  auth_header_value: "",
  request_template: JSON.stringify({ message: "{{prompt}}" }, null, 2),
  response_path: "$.response",
  timeout_seconds: 30,
  status: "DRAFT",
};

export function ApplicationForm({ mode }: { mode: "create" | "edit" }) {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const {
    data: workspaces,
    loading: loadingWorkspaces,
    error: workspacesError,
    reload: reloadWorkspaces,
  } = useApi(() => api.listWorkspaces(), []);
  const { data: existing, loading: loadingApp, error: loadError } = useApi(
    () => (mode === "edit" && id ? api.getApplication(id) : Promise.resolve(null)),
    [mode, id]
  );

  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null);
  const [testError, setTestError] = useState<string | null>(null);

  useEffect(() => {
    if (existing) {
      setForm({
        workspace_id: existing.workspace_id,
        name: existing.name,
        app_type: existing.app_type,
        description: existing.description || "",
        expected_behavior: existing.expected_behavior,
        forbidden_behavior: existing.forbidden_behavior,
        endpoint_url: existing.endpoint_url,
        auth_header_name: existing.auth_header_name || "",
        auth_header_value: "",
        request_template: JSON.stringify(existing.request_template ?? {}, null, 2),
        response_path: existing.response_path,
        timeout_seconds: existing.timeout_seconds,
        status: existing.status,
      });
    }
  }, [existing]);

  useEffect(() => {
    if (mode === "create" && workspaces && workspaces.length > 0 && !form.workspace_id) {
      setForm((f) => ({ ...f, workspace_id: workspaces[0].id }));
    }
  }, [mode, workspaces, form.workspace_id]);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function parseRequestTemplate(): Record<string, unknown> | null {
    try {
      const parsed = JSON.parse(form.request_template || "{}");
      setJsonError(null);
      return parsed;
    } catch (e) {
      setJsonError("Request template must be valid JSON.");
      return null;
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const template = parseRequestTemplate();
    if (template === null) return;

    setSaving(true);
    setSaveError(null);
    try {
      if (mode === "create") {
        const created = await api.createApplication({
          workspace_id: form.workspace_id,
          name: form.name,
          app_type: form.app_type,
          description: form.description || null,
          expected_behavior: form.expected_behavior,
          forbidden_behavior: form.forbidden_behavior,
          endpoint_url: form.endpoint_url,
          auth_header_name: form.auth_header_name || null,
          auth_header_value: form.auth_header_value || null,
          request_template: template,
          response_path: form.response_path,
          timeout_seconds: form.timeout_seconds,
          status: form.status,
        });
        navigate(`/applications/${created.id}`);
      } else if (id) {
        await api.updateApplication(id, {
          name: form.name,
          app_type: form.app_type,
          description: form.description || null,
          expected_behavior: form.expected_behavior,
          forbidden_behavior: form.forbidden_behavior,
          endpoint_url: form.endpoint_url,
          auth_header_name: form.auth_header_name || null,
          ...(form.auth_header_value ? { auth_header_value: form.auth_header_value } : {}),
          request_template: template,
          response_path: form.response_path,
          timeout_seconds: form.timeout_seconds,
          status: form.status,
        });
        navigate(`/applications/${id}`);
      }
    } catch (err) {
      setSaveError(err instanceof ApiError ? err.message : "Failed to save application");
    } finally {
      setSaving(false);
    }
  }

  async function handleTestConnection() {
    if (!id) return;
    setTesting(true);
    setTestError(null);
    setTestResult(null);
    try {
      const result = await api.testConnection(id);
      setTestResult(result);
    } catch (err) {
      setTestError(err instanceof ApiError ? err.message : "Connection test failed");
    } finally {
      setTesting(false);
    }
  }

  if (mode === "edit" && loadingApp) return <Loading label="Loading application…" />;
  if (mode === "edit" && loadError) return <ErrorState message={loadError} />;
  if (mode === "create" && loadingWorkspaces) return <Loading label="Loading workspaces…" />;
  if (mode === "create" && workspacesError) {
    return <ErrorState message={workspacesError} onRetry={reloadWorkspaces} />;
  }
  if (mode === "create" && !loadingWorkspaces && (!workspaces || workspaces.length === 0)) {
    return (
      <ErrorState message="No workspace exists yet. A workspace must be created via the API before registering applications (POST /api/workspaces)." />
    );
  }

  return (
    <div style={{ maxWidth: 720 }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">{mode === "create" ? "Add Application" : `Edit ${existing?.name ?? "Application"}`}</h1>
          <p className="page-subtitle">Register the AI app Plumbline will run assurance tests against.</p>
        </div>
      </div>

      <div style={{ marginBottom: 18 }}>
        <AuthorizedUseNotice compact />
      </div>

      <form onSubmit={handleSubmit} className="card">
        <div className="section-title">Identity</div>
        <div className="form-field">
          <label>Name</label>
          <input type="text" required value={form.name} onChange={(e) => update("name", e.target.value)} />
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <div className="form-field">
            <label>App Type</label>
            <select value={form.app_type} onChange={(e) => update("app_type", e.target.value as AppType)}>
              {APP_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div className="form-field">
            <label>Status</label>
            <select value={form.status} onChange={(e) => update("status", e.target.value as AppStatus)}>
              {APP_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="form-field">
          <label>Description</label>
          <textarea rows={2} value={form.description} onChange={(e) => update("description", e.target.value)} />
        </div>

        <div className="section-title">Behavior Contract</div>
        <div className="form-field">
          <label>Expected Behavior</label>
          <textarea
            rows={3}
            required
            placeholder="What should this app do, correctly and safely?"
            value={form.expected_behavior}
            onChange={(e) => update("expected_behavior", e.target.value)}
          />
        </div>
        <div className="form-field">
          <label>Forbidden Behavior</label>
          <textarea
            rows={3}
            required
            placeholder="What must this app never do (leak system prompt, take unauthorized actions, etc.)?"
            value={form.forbidden_behavior}
            onChange={(e) => update("forbidden_behavior", e.target.value)}
          />
        </div>

        <div className="section-title">Endpoint Configuration</div>
        <div className="form-field">
          <label>Endpoint URL</label>
          <input
            type="url"
            required
            placeholder="https://my-app.example.com/chat"
            value={form.endpoint_url}
            onChange={(e) => update("endpoint_url", e.target.value)}
          />
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <div className="form-field">
            <label>Auth Header Name</label>
            <input
              type="text"
              placeholder="Authorization"
              value={form.auth_header_name}
              onChange={(e) => update("auth_header_name", e.target.value)}
            />
          </div>
          <div className="form-field">
            <label>Auth Header Value</label>
            <input
              type="text"
              placeholder={mode === "edit" ? "Leave blank to keep existing" : "Bearer …"}
              value={form.auth_header_value}
              onChange={(e) => update("auth_header_value", e.target.value)}
            />
          </div>
        </div>
        <div className="form-field">
          <label>
            Request Template (JSON) <span className="hint">— use <code className="inline">{"{{prompt}}"}</code> where the attack prompt is substituted</span>
          </label>
          <textarea
            rows={5}
            value={form.request_template}
            onChange={(e) => update("request_template", e.target.value)}
            onBlur={parseRequestTemplate}
          />
          {jsonError && <span style={{ color: "var(--color-not-ready)", fontSize: 12 }}>{jsonError}</span>}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <div className="form-field">
            <label>
              Response Path <span className="hint">— JSONPath to the model's text in the response, e.g. <code className="inline">$.response</code></span>
            </label>
            <input type="text" value={form.response_path} onChange={(e) => update("response_path", e.target.value)} />
          </div>
          <div className="form-field">
            <label>Timeout (seconds)</label>
            <input
              type="number"
              min={1}
              value={form.timeout_seconds}
              onChange={(e) => update("timeout_seconds", Number(e.target.value))}
            />
          </div>
        </div>

        {mode === "edit" && (
          <>
            <div className="section-title">Connection</div>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 14 }}>
              <button type="button" className="btn" onClick={handleTestConnection} disabled={testing}>
                {testing ? "Testing…" : "Test Connection"}
              </button>
              {testResult && (
                <span style={{ color: testResult.ok ? "var(--color-ready)" : "var(--color-not-ready)", fontSize: 13 }}>
                  {testResult.ok ? "OK" : "Error"}
                  {testResult.latency_ms != null && ` · ${testResult.latency_ms}ms`}
                  {testResult.status_code != null && ` · HTTP ${testResult.status_code}`}
                  {testResult.error && ` · ${testResult.error}`}
                </span>
              )}
              {testError && <span style={{ color: "var(--color-not-ready)", fontSize: 13 }}>{testError}</span>}
            </div>
          </>
        )}

        {saveError && (
          <div className="error-state" style={{ marginBottom: 14 }}>
            {saveError}
          </div>
        )}

        <div style={{ display: "flex", gap: 10 }}>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "Saving…" : mode === "create" ? "Create Application" : "Save Changes"}
          </button>
          <button type="button" className="btn" onClick={() => navigate(-1)}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
