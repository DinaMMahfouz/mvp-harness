import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import { useApi } from "../lib/useApi";
import { Loading, ErrorState, EmptyState } from "../components/States";

async function loadRetestData(appId: string) {
  const [runs, comparisons] = await Promise.all([
    api.listRuns(appId),
    api.listComparisons(appId).catch(() => []),
  ]);
  const baseline = runs.find((r) => r.run_type === "BASELINE" && r.status === "COMPLETED") ?? runs[0] ?? null;
  return { runs, comparisons, baseline };
}

export function RetestComparisonPage() {
  const { id } = useParams<{ id: string }>();
  const { data, loading, error, reload } = useApi(() => loadRetestData(id!), [id]);
  const [scope, setScope] = useState<"failed_only" | "full_suite">("failed_only");
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [comparison, setComparison] = useState<Awaited<ReturnType<typeof api.createComparison>> | null>(null);

  async function runRetest() {
    if (!id || !data?.baseline) return;
    setRunning(true);
    setRunError(null);
    try {
      const retestRun = await api.retest(id, data.baseline.id, scope);
      // Poll until the retest run completes, then compute the comparison.
      let current = retestRun;
      for (let i = 0; i < 30 && current.status !== "COMPLETED" && current.status !== "FAILED"; i++) {
        await new Promise((r) => setTimeout(r, 2000));
        current = await api.getRun(retestRun.id);
      }
      if (current.status !== "COMPLETED") {
        throw new Error(`Retest run ended with status ${current.status}`);
      }
      const cmp = await api.createComparison(data.baseline.id, current.id);
      setComparison(cmp);
      reload();
    } catch (err) {
      setRunError(err instanceof ApiError || err instanceof Error ? err.message : "Retest failed");
    } finally {
      setRunning(false);
    }
  }

  if (loading) return <Loading label="Loading retest data…" />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return null;

  const latestComparison = comparison ?? data.comparisons[0] ?? null;
  const beforeScore = data.baseline?.assurance_score ?? null;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Retest & Comparison</h1>
          <p className="page-subtitle">Re-run the exact same versioned prompts and see what actually changed.</p>
        </div>
        <Link to={`/applications/${id}`} className="btn">
          Back to Application
        </Link>
      </div>

      {!data.baseline ? (
        <EmptyState title="No baseline run yet" description="Run assurance tests first before retesting." />
      ) : (
        <>
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="section-title">Trigger Retest</div>
            <div style={{ display: "flex", gap: 16, alignItems: "center", marginBottom: 14 }}>
              <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}>
                <input
                  type="radio"
                  checked={scope === "failed_only"}
                  onChange={() => setScope("failed_only")}
                />
                Retest Failed Only
              </label>
              <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}>
                <input type="radio" checked={scope === "full_suite"} onChange={() => setScope("full_suite")} />
                Full Suite
              </label>
            </div>
            <button className="btn btn-primary" onClick={runRetest} disabled={running}>
              {running ? "Retesting… (this can take a minute)" : "Run Retest"}
            </button>
            {runError && <div style={{ color: "var(--color-not-ready)", fontSize: 12.5, marginTop: 10 }}>{runError}</div>}
          </div>

          {latestComparison && (
            <div>
              <div style={{ display: "flex", gap: 24, alignItems: "center", marginBottom: 20 }}>
                <div style={{ textAlign: "center" }}>
                  <div className="muted" style={{ fontSize: 12 }}>
                    Before
                  </div>
                  <div style={{ fontSize: 38, fontWeight: 800 }}>{beforeScore != null ? beforeScore.toFixed(0) : "—"}</div>
                </div>
                <div style={{ fontSize: 24, color: "var(--color-text-faint)" }}>→</div>
                <div style={{ textAlign: "center" }}>
                  <div className="muted" style={{ fontSize: 12 }}>
                    After
                  </div>
                  <div style={{ fontSize: 38, fontWeight: 800, color: "var(--color-ready)" }}>
                    {comparison ? "recomputed" : "see run"}
                  </div>
                </div>
              </div>

              <div className="stat-row">
                <div className="stat-card">
                  <div className="stat-value" style={{ color: "var(--color-ready)" }}>
                    {latestComparison.fixed_count}
                  </div>
                  <div className="stat-label">Fixed</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value" style={{ color: "var(--sev-medium)" }}>
                    {latestComparison.remaining_count}
                  </div>
                  <div className="stat-label">Remaining</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value" style={{ color: "var(--color-not-ready)" }}>
                    {latestComparison.regression_count}
                  </div>
                  <div className="stat-label">Regression</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value" style={{ color: "var(--sev-high)" }}>
                    {latestComparison.new_count}
                  </div>
                  <div className="stat-label">New</div>
                </div>
              </div>

              <div className="section-title">Per-Test-Case Classification</div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Test Case</th>
                      <th>Classification</th>
                    </tr>
                  </thead>
                  <tbody>
                    {latestComparison.details.map((d, i) => (
                      <tr key={i}>
                        <td className="mono">{String((d as any).test_case_id ?? (d as any).id ?? i)}</td>
                        <td>{String((d as any).classification ?? (d as any).status ?? "—")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {!latestComparison && (
            <EmptyState title="No comparison yet" description="Run a retest above to generate a before/after comparison." />
          )}
        </>
      )}
    </div>
  );
}
