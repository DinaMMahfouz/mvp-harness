import { useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useApi } from "../lib/useApi";
import { supabase } from "../lib/supabaseClient";
import { Loading, ErrorState, EmptyState } from "../components/States";
import { DecisionBadge } from "../components/Badges";
import type { Application, Finding, ReleaseDecision } from "../types/models";

interface AppCardData {
  app: Application;
  latestDecision: ReleaseDecision | null;
  openCritical: number;
}

async function loadDashboard(): Promise<AppCardData[]> {
  const apps = await api.listApplications();
  return Promise.all(
    apps.map(async (app) => {
      const [decisions, findings] = await Promise.all([
        api.listReleaseDecisions(app.id).catch(() => [] as ReleaseDecision[]),
        api.listFindings(app.id).catch(() => [] as Finding[]),
      ]);
      const latestDecision = decisions[0] ?? null;
      const openCritical = findings.filter(
        (f) => f.severity === "CRITICAL" && (f.status === "OPEN" || f.status === "IN_PROGRESS")
      ).length;
      return { app, latestDecision, openCritical };
    })
  );
}

export function Dashboard() {
  const { data, loading, error, reload } = useApi(loadDashboard, []);

  // Real-time: a release decision or new CRITICAL finding made anywhere
  // (this session, a teammate's, or a retest completing) shows up on the
  // dashboard without a manual refresh.
  useEffect(() => {
    const channel = supabase
      .channel("dashboard-updates")
      .on("postgres_changes", { event: "*", schema: "public", table: "release_decisions" }, () => reload())
      .on("postgres_changes", { event: "*", schema: "public", table: "findings" }, () => reload())
      .subscribe();
    return () => {
      supabase.removeChannel(channel);
    };
  }, [reload]);

  const totals = useMemo(() => {
    if (!data) return { totalApps: 0, totalCritical: 0, blockedApps: 0 };
    return {
      totalApps: data.length,
      totalCritical: data.reduce((sum, d) => sum + d.openCritical, 0),
      blockedApps: data.filter((d) => d.latestDecision?.decision === "NOT_READY").length,
    };
  }, [data]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Is your AI application ready to ship? See it in seconds.</p>
        </div>
        <Link to="/applications/new" className="btn btn-primary">
          + Add Application
        </Link>
      </div>

      {loading && <Loading label="Loading applications…" />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {!loading && !error && data && data.length === 0 && (
        <EmptyState
          title="No applications registered yet"
          description="Register your first AI application to start running assurance tests."
          action={
            <Link to="/applications/new" className="btn btn-primary">
              Register an Application
            </Link>
          }
        />
      )}

      {!loading && !error && data && data.length > 0 && (
        <>
          <div className="stat-row">
            <div className="stat-card">
              <div className="stat-value">{totals.totalApps}</div>
              <div className="stat-label">Total Applications</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: totals.totalCritical > 0 ? "var(--color-not-ready)" : undefined }}>
                {totals.totalCritical}
              </div>
              <div className="stat-label">Open CRITICAL Findings</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: totals.blockedApps > 0 ? "var(--color-not-ready)" : undefined }}>
                {totals.blockedApps}
              </div>
              <div className="stat-label">Apps With Release Blockers</div>
            </div>
          </div>

          <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))" }}>
            {data.map(({ app, latestDecision, openCritical }) => (
              <Link key={app.id} to={`/applications/${app.id}`} className="card" style={{ display: "block", color: "inherit" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 15 }}>{app.name}</div>
                    <div className="muted" style={{ fontSize: 12, marginTop: 2 }}>
                      {app.app_type}
                    </div>
                  </div>
                </div>
                <div style={{ marginTop: 14 }}>
                  {latestDecision ? (
                    <DecisionBadge decision={latestDecision.decision} size="sm" />
                  ) : (
                    <span className="badge" style={{ color: "var(--color-text-faint)", background: "var(--color-bg-hover)" }}>
                      No decision yet
                    </span>
                  )}
                </div>
                {openCritical > 0 && (
                  <div style={{ marginTop: 10, fontSize: 12.5, color: "var(--color-not-ready)", fontWeight: 600 }}>
                    {openCritical} open CRITICAL finding{openCritical === 1 ? "" : "s"}
                  </div>
                )}
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
