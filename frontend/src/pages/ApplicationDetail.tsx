import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import { useApi } from "../lib/useApi";
import { Loading, ErrorState, EmptyState } from "../components/States";
import { AppStatusBadge, DecisionBadge, ResultBadge } from "../components/Badges";
import { AuthorizedUseNotice } from "../components/AuthorizedUseNotice";

type Tab = "overview" | "suites" | "runs" | "findings" | "hardening" | "reports";

async function loadDetail(appId: string) {
  const [app, suites, runs, findings, decisions] = await Promise.all([
    api.getApplication(appId),
    api.listTestSuites(appId),
    api.listRuns(appId),
    api.listFindings(appId),
    api.listReleaseDecisions(appId).catch(() => []),
  ]);
  return { app, suites, runs, findings, decisions };
}

export function ApplicationDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>("overview");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const { data, loading, error, reload } = useApi(() => loadDetail(id!), [id]);

  async function handleGenerateOrRun() {
    if (!id || !data) return;
    setBusy(true);
    setActionError(null);
    try {
      if (data.suites.length === 0) {
        await api.generateTestPlan(id);
        reload();
      } else {
        const activeSuite = data.suites.find((s) => s.is_active) ?? data.suites[0];
        const run = await api.executeRun(id, activeSuite.id);
        navigate(`/runs/${run.id}`);
      }
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Loading label="Loading application…" />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return null;

  const { app, suites, runs, findings, decisions } = data;
  const latestDecision = decisions[0] ?? null;
  const openCounts = {
    CRITICAL: findings.filter((f) => f.severity === "CRITICAL" && f.status !== "RESOLVED").length,
    HIGH: findings.filter((f) => f.severity === "HIGH" && f.status !== "RESOLVED").length,
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <h1 className="page-title">{app.name}</h1>
            <AppStatusBadge status={app.status} />
          </div>
          <p className="page-subtitle">
            {app.app_type} · {app.endpoint_url}
          </p>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          {latestDecision && <DecisionBadge decision={latestDecision.decision} />}
          <button className="btn btn-primary" onClick={handleGenerateOrRun} disabled={busy}>
            {busy ? "Working…" : suites.length === 0 ? "Generate Test Plan" : "Run Assurance"}
          </button>
          <Link to={`/applications/${app.id}/edit`} className="btn">
            Edit
          </Link>
        </div>
      </div>

      <div style={{ marginBottom: 16 }}>
        <AuthorizedUseNotice compact />
      </div>

      {actionError && (
        <div className="error-state" style={{ marginBottom: 16 }}>
          {actionError}
        </div>
      )}

      {(openCounts.CRITICAL > 0 || openCounts.HIGH > 0) && (
        <div className="stat-row">
          <div className="stat-card">
            <div className="stat-value" style={{ color: "var(--color-not-ready)" }}>
              {openCounts.CRITICAL}
            </div>
            <div className="stat-label">Open CRITICAL Findings</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ color: "var(--sev-high)" }}>
              {openCounts.HIGH}
            </div>
            <div className="stat-label">Open HIGH Findings</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{runs.length}</div>
            <div className="stat-label">Total Runs</div>
          </div>
        </div>
      )}

      <div className="tabs">
        {(["overview", "suites", "runs", "findings", "hardening", "reports"] as Tab[]).map((t) => (
          <div key={t} className={"tab" + (tab === t ? " active" : "")} onClick={() => setTab(t)}>
            {t === "suites" ? "Test Suites" : t.charAt(0).toUpperCase() + t.slice(1)}
          </div>
        ))}
      </div>

      {tab === "overview" && (
        <div className="grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
          <div className="card">
            <div className="section-title">Release Decision</div>
            {latestDecision ? (
              <>
                <DecisionBadge decision={latestDecision.decision} size="lg" />
                <p style={{ marginTop: 14, fontSize: 13.5 }}>{latestDecision.rationale}</p>
                <p className="muted" style={{ marginTop: 10, fontSize: 12.5 }}>
                  {latestDecision.blocking_findings_count} blocking finding(s) · score {latestDecision.assurance_score.toFixed(0)}/100
                </p>
                <Link to={`/applications/${app.id}/release-decision`} className="btn btn-sm" style={{ marginTop: 12 }}>
                  View full decision trace
                </Link>
              </>
            ) : (
              <EmptyState title="No release decision yet" description="Run assurance tests, then compute a release decision." />
            )}
          </div>
          <div className="card">
            <div className="section-title">Behavior Contract</div>
            <p style={{ fontSize: 13, marginBottom: 10 }}>
              <strong>Expected:</strong> {app.expected_behavior}
            </p>
            <p style={{ fontSize: 13 }}>
              <strong>Forbidden:</strong> {app.forbidden_behavior}
            </p>
            {app.description && (
              <p className="muted" style={{ fontSize: 13, marginTop: 10 }}>
                {app.description}
              </p>
            )}
          </div>
        </div>
      )}

      {tab === "suites" && (
        <div>
          {suites.length === 0 ? (
            <EmptyState title="No test suite yet" description="Generate a test plan to get started." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Source</th>
                    <th>Active</th>
                    <th>Generated</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {suites.map((s) => (
                    <tr key={s.id}>
                      <td style={{ fontWeight: 600 }}>{s.name}</td>
                      <td>{s.source}</td>
                      <td>{s.is_active ? "Yes" : "No"}</td>
                      <td className="muted">{new Date(s.generated_at).toLocaleString()}</td>
                      <td>
                        <Link to={`/applications/${app.id}/test-plan`} className="btn btn-sm">
                          View Test Plan
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === "runs" && (
        <div>
          {runs.length === 0 ? (
            <EmptyState title="No runs yet" description="Run assurance tests once a test plan exists." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Score</th>
                    <th>Triggered By</th>
                    <th>Created</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map((r) => (
                    <tr key={r.id}>
                      <td>{r.run_type}</td>
                      <td>{r.status}</td>
                      <td>{r.assurance_score != null ? r.assurance_score.toFixed(0) : "—"}</td>
                      <td>{r.triggered_by}</td>
                      <td className="muted">{new Date(r.created_at).toLocaleString()}</td>
                      <td>
                        <Link to={`/runs/${r.id}`} className="btn btn-sm">
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === "findings" && (
        <div>
          <p style={{ marginBottom: 14 }}>
            <Link to={`/applications/${app.id}/findings`} className="btn btn-primary">
              Open Findings Board
            </Link>
          </p>
          {findings.length === 0 ? (
            <EmptyState title="No findings" description="Run assurance tests to surface findings." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Severity</th>
                    <th>Title</th>
                    <th>Category</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {findings.slice(0, 8).map((f) => (
                    <tr key={f.id}>
                      <td>{f.severity}</td>
                      <td>
                        <Link to={`/findings/${f.id}`}>{f.title}</Link>
                      </td>
                      <td className="muted">{f.category}</td>
                      <td>{f.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === "hardening" && (
        <div className="card">
          <div className="section-title">Harden → Retest → Release</div>
          <p style={{ fontSize: 13.5, marginBottom: 14 }}>
            Resolve findings, then retest the exact same versioned prompts to prove the fix worked without
            introducing regressions.
          </p>
          <ResultBadge result="FAIL" /> <span className="muted" style={{ fontSize: 12.5 }}>→</span>{" "}
          <ResultBadge result="PASS" />
          <div style={{ marginTop: 16 }}>
            <Link to={`/applications/${app.id}/retest`} className="btn btn-primary">
              Go to Retest & Comparison
            </Link>
          </div>
        </div>
      )}

      {tab === "reports" && (
        <div className="card">
          <div className="section-title">Reports</div>
          <p style={{ fontSize: 13.5, marginBottom: 14 }}>Export the full issue register as an Excel workbook.</p>
          <Link to={`/applications/${app.id}/reports`} className="btn btn-primary">
            Go to Reports
          </Link>
        </div>
      )}
    </div>
  );
}
