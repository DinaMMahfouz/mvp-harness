import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import { useApi } from "../lib/useApi";
import { supabase } from "../lib/supabaseClient";
import { Loading, ErrorState, EmptyState } from "../components/States";
import { DecisionBadge, ResultBadge, SeverityBadge } from "../components/Badges";
import type { ReleaseDecision } from "../types/models";

async function loadRun(runId: string) {
  const [run, results] = await Promise.all([api.getRun(runId), api.getRunResults(runId)]);
  let decision: ReleaseDecision | null = null;
  try {
    decision = await api.getLatestReleaseDecisionForRun(runId);
  } catch {
    decision = null;
  }
  return { run, results, decision };
}

function ResultRow({ result }: { result: Awaited<ReturnType<typeof loadRun>>["results"][number] }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <tr style={{ cursor: "pointer" }} onClick={() => setOpen((v) => !v)}>
        <td>
          <ResultBadge result={result.result} />
        </td>
        <td>
          <SeverityBadge severity={result.severity} />
        </td>
        <td>{(result.confidence * 100).toFixed(0)}%</td>
        <td className="muted mono" style={{ maxWidth: 320, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {result.execution_prompt}
        </td>
        <td>{open ? "▲" : "▼"}</td>
      </tr>
      {open && (
        <tr>
          <td colSpan={5} style={{ background: "var(--color-bg-elevated)" }}>
            <div style={{ padding: "10px 4px" }}>
              <div className="section-title">Execution Prompt</div>
              <p className="mono" style={{ whiteSpace: "pre-wrap", marginBottom: 12 }}>
                {result.execution_prompt}
              </p>
              <div className="section-title">Model Response</div>
              <p className="mono" style={{ whiteSpace: "pre-wrap", marginBottom: 12 }}>
                {result.model_response || "(no response captured)"}
              </p>
              <div className="section-title">Evidence</div>
              <pre className="mono" style={{ whiteSpace: "pre-wrap", marginBottom: 12 }}>
                {JSON.stringify(result.evidence, null, 2)}
              </pre>
              <p className="muted" style={{ fontSize: 12 }}>
                evaluator: {result.evaluator_version} · http {result.http_status ?? "—"} · latency{" "}
                {result.latency_ms != null ? `${result.latency_ms}ms` : "—"}
              </p>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

export function RunDetail() {
  const { id } = useParams<{ id: string }>();
  const { data, loading, error, reload } = useApi(() => loadRun(id!), [id]);
  const [recomputing, setRecomputing] = useState(false);
  const [decision, setDecision] = useState<ReleaseDecision | null>(null);
  const [decisionError, setDecisionError] = useState<string | null>(null);

  useEffect(() => {
    if (data) setDecision(data.decision);
  }, [data]);

  // Real-time: reload the moment Postgres actually changes, instead of
  // guessing with a poll interval. Subscribed for the life of the page (not
  // just while "in progress") so a result edited/added from elsewhere - or
  // a race where the run finished between the initial load and this effect
  // mounting - is still picked up.
  useEffect(() => {
    if (!id) return;
    const channel = supabase
      .channel(`run-${id}`)
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "test_results", filter: `test_run_id=eq.${id}` },
        () => reload()
      )
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "test_runs", filter: `id=eq.${id}` },
        () => reload()
      )
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "release_decisions", filter: `test_run_id=eq.${id}` },
        () => reload()
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [id, reload]);

  // Fallback poll, only while the run is actively in progress: Realtime
  // delivery isn't guaranteed (a dropped websocket, a brief reconnect), and
  // this is the one view where a stuck "RUNNING" status because of a missed
  // event would be actively misleading about whether assurance is real.
  useEffect(() => {
    if (!data || (data.run.status !== "PENDING" && data.run.status !== "RUNNING")) return;
    const t = setInterval(() => reload(), 5000);
    return () => clearInterval(t);
  }, [data, reload]);

  async function recompute() {
    if (!id) return;
    setRecomputing(true);
    setDecisionError(null);
    try {
      const d = await api.recomputeReleaseDecision(id);
      setDecision(d);
    } catch (err) {
      setDecisionError(err instanceof ApiError ? err.message : "Failed to compute release decision");
    } finally {
      setRecomputing(false);
    }
  }

  if (loading) return <Loading label="Loading run…" />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return null;

  const { run, results } = data;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            {run.run_type} Run — {run.status}
          </h1>
          <p className="page-subtitle">
            Triggered by {run.triggered_by} · {new Date(run.created_at).toLocaleString()}
          </p>
        </div>
        <Link to={`/applications/${run.application_id}`} className="btn">
          Back to Application
        </Link>
      </div>

      {(run.status === "PENDING" || run.status === "RUNNING") && (
        <div className="loading-state" style={{ marginBottom: 16 }}>
          Run in progress — refreshing automatically…
        </div>
      )}

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="section-title">Release Decision</div>
        {decision ? (
          <>
            <DecisionBadge decision={decision.decision} size="lg" />
            <p style={{ marginTop: 14, fontSize: 13.5 }}>{decision.rationale}</p>
            <p className="muted" style={{ marginTop: 10, fontSize: 12.5 }}>
              {decision.blocking_findings_count} blocking finding(s)
              {decision.conditions.length > 0 && ` · ${decision.conditions.length} condition(s)`} · score{" "}
              {decision.assurance_score.toFixed(0)}/100
            </p>
            {decision.conditions.length > 0 && (
              <ul style={{ marginTop: 10, paddingLeft: 18, fontSize: 13 }}>
                {decision.conditions.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            )}
          </>
        ) : (
          <p className="muted" style={{ fontSize: 13 }}>No release decision computed for this run yet.</p>
        )}
        {decisionError && <div style={{ color: "var(--color-not-ready)", fontSize: 12.5, marginTop: 8 }}>{decisionError}</div>}
        <button className="btn btn-sm" style={{ marginTop: 12 }} onClick={recompute} disabled={recomputing || run.status !== "COMPLETED"}>
          {recomputing ? "Computing…" : "Recompute"}
        </button>
        {run.status !== "COMPLETED" && (
          <span className="muted" style={{ fontSize: 12, marginLeft: 10 }}>
            Available once the run completes.
          </span>
        )}
      </div>

      <div className="section-title">Results ({results.length})</div>
      {results.length === 0 ? (
        <EmptyState title="No results yet" description="Results will appear as the run executes." />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Result</th>
                <th>Severity</th>
                <th>Confidence</th>
                <th>Prompt</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {results.map((r) => (
                <ResultRow key={r.id} result={r} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
