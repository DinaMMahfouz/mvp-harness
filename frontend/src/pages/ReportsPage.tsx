import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import { useApi } from "../lib/useApi";
import { Loading, ErrorState } from "../components/States";

export function ReportsPage() {
  const { id } = useParams<{ id: string }>();
  const { data: app, loading, error, reload } = useApi(() => api.getApplication(id!), [id]);
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  async function download() {
    if (!app) return;
    setDownloading(true);
    setDownloadError(null);
    try {
      await api.exportExcel(app.id, app.name);
    } catch (err) {
      setDownloadError(err instanceof ApiError ? err.message : "Failed to export report");
    } finally {
      setDownloading(false);
    }
  }

  if (loading) return <Loading label="Loading…" />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!app) return null;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Reports</h1>
          <p className="page-subtitle">Export the issue register for {app.name}.</p>
        </div>
        <Link to={`/applications/${id}`} className="btn">
          Back to Application
        </Link>
      </div>

      <div className="card" style={{ maxWidth: 480 }}>
        <div className="section-title">Excel Issue Register</div>
        <p style={{ fontSize: 13.5, marginBottom: 16 }}>
          A 4-sheet workbook covering findings, test results, remediation history, and release decisions —
          suitable for sharing with stakeholders who don't use HARNESS directly.
        </p>
        {downloadError && <div style={{ color: "var(--color-not-ready)", fontSize: 12.5, marginBottom: 12 }}>{downloadError}</div>}
        <button className="btn btn-primary" onClick={download} disabled={downloading}>
          {downloading ? "Preparing download…" : "Download Excel Issue Register"}
        </button>
      </div>
    </div>
  );
}
