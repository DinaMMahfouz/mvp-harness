import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useApi } from "../lib/useApi";
import { Loading, ErrorState, EmptyState } from "../components/States";
import { AppStatusBadge } from "../components/Badges";
import { APP_STATUSES, APP_TYPES, type AppStatus, type AppType } from "../types/enums";

export function ApplicationRegistry() {
  const [search, setSearch] = useState("");
  const [appType, setAppType] = useState<AppType | "">("");
  const [status, setStatus] = useState<AppStatus | "">("");

  const { data, loading, error, reload } = useApi(
    () => api.listApplications({ search: search || undefined, app_type: (appType as AppType) || undefined }),
    [search, appType]
  );

  // NOTE: the backend's GET /applications route only supports workspace_id/app_type/search
  // query params (no `status`) — see docs/agent-team-decision-log.md. Filtered client-side here.
  const filtered = useMemo(() => {
    if (!data) return [];
    if (!status) return data;
    return data.filter((a) => a.status === status);
  }, [data, status]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Application Registry</h1>
          <p className="page-subtitle">All registered AI applications under assurance testing.</p>
        </div>
        <Link to="/applications/new" className="btn btn-primary">
          + Add Application
        </Link>
      </div>

      <div className="card" style={{ display: "flex", gap: 12, marginBottom: 18, flexWrap: "wrap", padding: 14 }}>
        <input
          type="text"
          placeholder="Search by name…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ maxWidth: 260 }}
        />
        <select value={appType} onChange={(e) => setAppType(e.target.value as AppType | "")} style={{ maxWidth: 180 }}>
          <option value="">All types</option>
          {APP_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value as AppStatus | "")} style={{ maxWidth: 180 }}>
          <option value="">All statuses</option>
          {APP_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      {loading && <Loading label="Loading applications…" />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {!loading && !error && filtered.length === 0 && (
        <EmptyState
          title="No applications match"
          description="Try a different search or filter, or register a new application."
          action={
            <Link to="/applications/new" className="btn btn-primary">
              Register an Application
            </Link>
          }
        />
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Status</th>
                <th>Endpoint</th>
                <th>Last Connection Test</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((app) => (
                <tr key={app.id}>
                  <td>
                    <Link to={`/applications/${app.id}`} style={{ fontWeight: 600, color: "var(--color-text)" }}>
                      {app.name}
                    </Link>
                  </td>
                  <td>{app.app_type}</td>
                  <td>
                    <AppStatusBadge status={app.status} />
                  </td>
                  <td className="mono muted" style={{ maxWidth: 260, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {app.endpoint_url}
                  </td>
                  <td>
                    {app.last_connection_test_at ? (
                      <span style={{ color: app.last_connection_test_ok ? "var(--color-ready)" : "var(--color-not-ready)" }}>
                        {app.last_connection_test_ok ? "OK" : "Failed"} · {new Date(app.last_connection_test_at).toLocaleString()}
                      </span>
                    ) : (
                      <span className="muted">Never tested</span>
                    )}
                  </td>
                  <td>
                    <Link to={`/applications/${app.id}/edit`} className="btn btn-sm">
                      Edit
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
