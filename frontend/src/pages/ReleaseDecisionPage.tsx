import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import { useApi } from "../lib/useApi";
import { Loading, ErrorState, EmptyState } from "../components/States";
import { DecisionBadge } from "../components/Badges";

async function loadDecisions(appId: string) {
  const [decisions, runs] = await Promise.all([
    api.listReleaseDecisions(appId),
    api.listRuns(appId),
  ]);
  return { decisions, runs };
}

export function ReleaseDecisionPage() {
  const { id } = useParams<{ id: string }>();
  const { data, loading, error, reload } = useApi(() => loadDecisions(id!), [id]);
  const [recomputing, setRecomputing] = useState(false);
  const [recomputeError, setRecomputeError] = useState<string | null>(null);

  async function recompute() {
    if (!data) return;
    const latestRun = data.runs.find((r) => r.status === "COMPLETED");
    if (!latestRun) {
      setRecomputeError("No completed run to compute a decision for.");
      return;
    }
    setRecomputing(true);
    setRecomputeError(null);
    try {
      await api.recomputeReleaseDecision(latestRun.id);
      reload();
    } catch (err) {
      setRecomputeError(err instanceof ApiError ? err.message : "Failed to recompute");
    } finally {
      setRecomputing(false);
    }
  }

  if (loading) return <Loading label="Loading release decisions…" />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return null;

  const latest = data.decisions[0] ?? null;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Release Decision</h1>
          <p className="page-subtitle">The hero call: is this application ready to ship, and why.</p>
        </div>
        <Link to={`/applications/${id}`} className="btn">
          Back to Application
        </Link>
      </div>

      {!latest ? (
        <EmptyState
          title="No release decision computed yet"
          description="Run assurance tests to completion, then compute a decision."
          action={
            <button className="btn btn-primary" onClick={recompute} disabled={recomputing}>
              {recomputing ? "Computing…" : "Compute Release Decision"}
            </button>
          }
        />
      ) : (
        <div className="card">
          <DecisionBadge decision={latest.decision} size="lg" />
          <p style={{ marginTop: 18, fontSize: 15, lineHeight: 1.6 }}>{latest.rationale}</p>

          <div className="stat-row" style={{ marginTop: 20 }}>
            <div className="stat-card">
              <div className="stat-value">{latest.blocking_findings_count}</div>
              <div className="stat-label">Blocking Findings</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{latest.assurance_score.toFixed(0)}</div>
              <div className="stat-label">Assurance Score</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{latest.conditions.length}</div>
              <div className="stat-label">Conditions</div>
            </div>
          </div>

          {latest.conditions.length > 0 && (
            <>
              <div className="section-title">Conditions</div>
              <ul style={{ paddingLeft: 18, fontSize: 13.5 }}>
                {latest.conditions.map((c, i) => (
                  <li key={i} style={{ marginBottom: 6 }}>
                    {c}
                  </li>
                ))}
              </ul>
            </>
          )}

          <p className="muted" style={{ fontSize: 12, marginTop: 16 }}>
            Decided {new Date(latest.decided_at).toLocaleString()}
          </p>

          {recomputeError && <div style={{ color: "var(--color-not-ready)", fontSize: 12.5, marginTop: 10 }}>{recomputeError}</div>}
          <button className="btn btn-sm" style={{ marginTop: 14 }} onClick={recompute} disabled={recomputing}>
            {recomputing ? "Computing…" : "Recompute"}
          </button>
        </div>
      )}

      {data.decisions.length > 1 && (
        <div style={{ marginTop: 24 }}>
          <div className="section-title">History</div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Decision</th>
                  <th>Score</th>
                  <th>Blocking</th>
                  <th>Decided</th>
                </tr>
              </thead>
              <tbody>
                {data.decisions.map((d) => (
                  <tr key={d.id}>
                    <td>
                      <DecisionBadge decision={d.decision} size="sm" />
                    </td>
                    <td>{d.assurance_score.toFixed(0)}</td>
                    <td>{d.blocking_findings_count}</td>
                    <td className="muted">{new Date(d.decided_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
