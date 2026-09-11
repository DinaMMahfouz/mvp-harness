import type { ReactNode } from "react";

export function Loading({ label = "Loading…" }: { label?: string }) {
  return <div className="loading-state">{label}</div>;
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="error-state">
      <p style={{ fontWeight: 650, marginBottom: 6 }}>Something went wrong</p>
      <p style={{ fontSize: 13 }}>{message}</p>
      {onRetry && (
        <button className="btn btn-sm" style={{ marginTop: 12 }} onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <p style={{ fontWeight: 650, color: "var(--color-text)", marginBottom: 6 }}>{title}</p>
      {description && <p style={{ fontSize: 13, marginBottom: action ? 14 : 0 }}>{description}</p>}
      {action}
    </div>
  );
}
