import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import { useApi } from "../lib/useApi";
import { Loading, ErrorState, EmptyState } from "../components/States";
import { SeverityBadge } from "../components/Badges";
import { CATEGORY_GROUP, SEVERITY_LEVELS, type CategoryGroup, type SeverityLevel } from "../types/enums";
import type { TestCase } from "../types/models";

async function loadPlan(appId: string) {
  const suites = await api.listTestSuites(appId);
  const suite = suites.find((s) => s.is_active) ?? suites[0] ?? null;
  const cases = suite ? await api.listTestCases(suite.id) : [];
  return { suite, cases };
}

function EditableCase({ testCase, onSaved }: { testCase: TestCase; onSaved: (c: TestCase) => void }) {
  const [editing, setEditing] = useState(false);
  const [prompt, setPrompt] = useState(testCase.attack_prompt);
  const [severity, setSeverity] = useState<SeverityLevel>(testCase.severity_if_failed);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function toggleEnabled() {
    try {
      const updated = await api.editTestCase(testCase.id, { enabled: !testCase.enabled });
      onSaved(updated);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Failed to update");
    }
  }

  async function save() {
    setSaving(true);
    setErr(null);
    try {
      const updated = await api.editTestCase(testCase.id, {
        attack_prompt: prompt,
        severity_if_failed: severity,
      });
      onSaved(updated);
      setEditing(false);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card" style={{ opacity: testCase.enabled ? 1 : 0.5 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <SeverityBadge severity={testCase.severity_if_failed} />
          <span className="muted" style={{ fontSize: 12 }}>
            v{testCase.version} {testCase.is_locked && "· locked (edits create a new version)"}
          </span>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12.5 }}>
            <input type="checkbox" checked={testCase.enabled} onChange={toggleEnabled} />
            Enabled
          </label>
          <button className="btn btn-sm" onClick={() => setEditing((v) => !v)}>
            {editing ? "Cancel" : "Edit"}
          </button>
        </div>
      </div>

      {!editing ? (
        <>
          <p className="mono" style={{ marginTop: 12, whiteSpace: "pre-wrap" }}>
            {testCase.attack_prompt}
          </p>
          <p className="muted" style={{ marginTop: 8, fontSize: 12.5 }}>
            Expected safe behavior: {testCase.expected_safe_behavior}
          </p>
        </>
      ) : (
        <div style={{ marginTop: 12 }}>
          <div className="form-field">
            <label>Attack Prompt</label>
            <textarea rows={3} value={prompt} onChange={(e) => setPrompt(e.target.value)} />
          </div>
          <div className="form-field" style={{ maxWidth: 200 }}>
            <label>Severity if Failed</label>
            <select value={severity} onChange={(e) => setSeverity(e.target.value as SeverityLevel)}>
              {SEVERITY_LEVELS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          {err && <div style={{ color: "var(--color-not-ready)", fontSize: 12.5, marginBottom: 10 }}>{err}</div>}
          <button className="btn btn-primary btn-sm" onClick={save} disabled={saving}>
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      )}
    </div>
  );
}

export function TestPlan() {
  const { id } = useParams<{ id: string }>();
  const { data, loading, error, reload } = useApi(() => loadPlan(id!), [id]);
  const [cases, setCases] = useState<TestCase[] | null>(null);

  const effectiveCases = cases ?? data?.cases ?? [];

  const grouped = useMemo(() => {
    const groups: Record<CategoryGroup, TestCase[]> = { Security: [], Reliability: [], Control: [] };
    for (const c of effectiveCases) {
      groups[CATEGORY_GROUP[c.category]].push(c);
    }
    return groups;
  }, [effectiveCases]);

  function handleSaved(updated: TestCase) {
    setCases((prev) => (prev ?? data?.cases ?? []).map((c) => (c.id === updated.id ? updated : c)));
  }

  if (loading) return <Loading label="Loading test plan…" />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data || !data.suite) {
    return (
      <EmptyState
        title="No test plan generated yet"
        description="Go to the application's Overview tab and click Generate Test Plan."
        action={
          <Link to={`/applications/${id}`} className="btn btn-primary">
            Back to Application
          </Link>
        }
      />
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Test Plan — {data.suite.name}</h1>
          <p className="page-subtitle">
            {effectiveCases.length} test cases across Security, Reliability, and Control.
          </p>
        </div>
        <Link to={`/applications/${id}`} className="btn">
          Back to Application
        </Link>
      </div>

      {(["Security", "Reliability", "Control"] as CategoryGroup[]).map((group) => (
        <div key={group}>
          <div className="section-title">
            {group} ({grouped[group].length})
          </div>
          {grouped[group].length === 0 ? (
            <p className="muted" style={{ fontSize: 13, marginBottom: 16 }}>
              No test cases in this group.
            </p>
          ) : (
            <div className="grid" style={{ marginBottom: 16 }}>
              {grouped[group].map((c) => (
                <EditableCase key={c.id} testCase={c} onSaved={handleSaved} />
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
