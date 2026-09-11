import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import { useApi } from "../lib/useApi";
import { Loading, ErrorState } from "../components/States";
import { FindingStatusBadge, SeverityBadge } from "../components/Badges";
import type { FindingStatus } from "../types/enums";

async function loadFinding(findingId: string) {
  const [finding, remediations] = await Promise.all([
    api.getFinding(findingId),
    api.listRemediations(findingId),
  ]);
  return { finding, remediations };
}

const TRANSITIONS: { status: FindingStatus; label: string }[] = [
  { status: "IN_PROGRESS", label: "Mark In Progress" },
  { status: "RESOLVED", label: "Mark Resolved" },
  { status: "ACCEPT_RISK", label: "Accept Risk" },
];

export function FindingDetail() {
  const { id } = useParams<{ id: string }>();
  const { data, loading, error, reload } = useApi(() => loadFinding(id!), [id]);
  const [note, setNote] = useState("");
  const [changedBy, setChangedBy] = useState("dinamamdouhhh@gmail.com");
  const [busy, setBusy] = useState<FindingStatus | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  async function transition(status: FindingStatus) {
    if (!id) return;
    setBusy(status);
    setActionError(null);
    try {
      await api.updateFindingStatus(id, { status, note: note || null, changed_by: changedBy || "unknown" });
      setNote("");
      reload();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Failed to update finding");
    } finally {
      setBusy(null);
    }
  }

  if (loading) return <Loading label="Loading finding…" />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return null;

  const { finding, remediations } = data;

  return (
    <div>
      <div className="page-header">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <SeverityBadge severity={finding.severity} />
            <FindingStatusBadge status={finding.status} />
          </div>
          <h1 className="page-title" style={{ marginTop: 8 }}>
            {finding.title}
          </h1>
          <p className="page-subtitle">{finding.category}</p>
        </div>
        <Link to={`/applications/${finding.application_id}/findings`} className="btn">
          Back to Findings
        </Link>
      </div>

      <div className="grid" style={{ gridTemplateColumns: "2fr 1fr" }}>
        <div>
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="section-title">Root Cause</div>
            <p style={{ fontSize: 13.5 }}>{finding.root_cause}</p>
            <div className="section-title">Recommendation</div>
            <p style={{ fontSize: 13.5 }}>{finding.recommendation}</p>
          </div>

          <div className="card">
            <div className="section-title">Remediation History</div>
            {remediations.length === 0 ? (
              <p className="muted" style={{ fontSize: 13 }}>No status changes recorded yet.</p>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Status</th>
                      <th>Note</th>
                      <th>Changed By</th>
                      <th>When</th>
                    </tr>
                  </thead>
                  <tbody>
                    {remediations.map((r) => (
                      <tr key={r.id}>
                        <td>
                          <FindingStatusBadge status={r.status} />
                        </td>
                        <td>{r.note || "—"}</td>
                        <td className="muted">{r.changed_by}</td>
                        <td className="muted">{new Date(r.changed_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="section-title">Update Status</div>
          <div className="form-field">
            <label>Changed By</label>
            <input type="text" value={changedBy} onChange={(e) => setChangedBy(e.target.value)} />
          </div>
          <div className="form-field">
            <label>Note</label>
            <textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} placeholder="What did you change or why is this risk accepted?" />
          </div>
          {actionError && <div style={{ color: "var(--color-not-ready)", fontSize: 12.5, marginBottom: 10 }}>{actionError}</div>}
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {TRANSITIONS.map((t) => (
              <button
                key={t.status}
                className="btn btn-sm"
                disabled={busy !== null || finding.status === t.status}
                onClick={() => transition(t.status)}
              >
                {busy === t.status ? "Saving…" : t.label}
              </button>
            ))}
          </div>
          <p className="muted" style={{ fontSize: 11.5, marginTop: 14 }}>
            Finding evidence (attack prompt, model response, and raw evidence) lives on the underlying test
            result — view it in the Run Detail page for run that first surfaced this finding.
          </p>
          <Link to={`/runs/${finding.first_seen_run_id}`} className="btn btn-sm" style={{ marginTop: 6 }}>
            View First-Seen Run
          </Link>
        </div>
      </div>
    </div>
  );
}
