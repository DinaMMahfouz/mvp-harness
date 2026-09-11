import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { useApi } from "../lib/useApi";
import { Loading, ErrorState, EmptyState } from "../components/States";
import { FindingStatusBadge, SeverityBadge } from "../components/Badges";
import { FINDING_STATUSES, SEVERITY_LEVELS, type FindingStatus, type SeverityLevel } from "../types/enums";

export function FindingsBoard() {
  const { id } = useParams<{ id: string }>();
  const [status, setStatus] = useState<FindingStatus | "">("");

  const { data, loading, error, reload } = useApi(
    () => api.listFindings(id!, (status as FindingStatus) || undefined),
    [id, status]
  );

  const bySeverity = useMemo(() => {
    const groups: Record<SeverityLevel, NonNullable<typeof data>> = {
      CRITICAL: [],
      HIGH: [],
      MEDIUM: [],
      LOW: [],
      INFO: [],
    };
    for (const f of data ?? []) {
      groups[f.severity].push(f);
    }
    return groups;
  }, [data]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Findings Board</h1>
          <p className="page-subtitle">Evidence-backed issues grouped by severity — worst first.</p>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <select value={status} onChange={(e) => setStatus(e.target.value as FindingStatus | "")}>
            <option value="">All statuses</option>
            {FINDING_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <Link to={`/applications/${id}`} className="btn">
            Back to Application
          </Link>
        </div>
      </div>

      {loading && <Loading label="Loading findings…" />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {!loading && !error && data && data.length === 0 && (
        <EmptyState title="No findings" description="Nothing here — run assurance tests, or adjust the status filter." />
      )}

      {!loading &&
        !error &&
        data &&
        data.length > 0 &&
        (Object.keys(bySeverity) as SeverityLevel[])
          .filter((sev) => SEVERITY_LEVELS.includes(sev) && bySeverity[sev].length > 0)
          .sort((a, b) => SEVERITY_LEVELS.indexOf(b) - SEVERITY_LEVELS.indexOf(a))
          .map((sev) => (
            <div key={sev} style={{ marginBottom: 20 }}>
              <div className="section-title">
                {sev} ({bySeverity[sev].length})
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Title</th>
                      <th>Category</th>
                      <th>Status</th>
                      <th>First Seen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bySeverity[sev].map((f) => (
                      <tr key={f.id}>
                        <td>
                          <Link to={`/findings/${f.id}`} style={{ fontWeight: 600, color: "var(--color-text)" }}>
                            {f.title}
                          </Link>
                        </td>
                        <td className="muted">{f.category}</td>
                        <td>
                          <FindingStatusBadge status={f.status} />
                        </td>
                        <td className="muted">{new Date(f.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
    </div>
  );
}
