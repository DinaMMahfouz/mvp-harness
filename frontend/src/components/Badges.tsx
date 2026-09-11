import type { AppStatus, FindingStatus, ReleaseDecisionEnum, ResultStatus, SeverityLevel } from "../types/enums";

export function SeverityBadge({ severity }: { severity: SeverityLevel }) {
  const map: Record<SeverityLevel, { color: string; bg: string }> = {
    INFO: { color: "var(--sev-info)", bg: "var(--sev-info-bg)" },
    LOW: { color: "var(--sev-low)", bg: "var(--sev-low-bg)" },
    MEDIUM: { color: "var(--sev-medium)", bg: "var(--sev-medium-bg)" },
    HIGH: { color: "var(--sev-high)", bg: "var(--sev-high-bg)" },
    CRITICAL: { color: "var(--sev-critical)", bg: "var(--sev-critical-bg)" },
  };
  const s = map[severity];
  return (
    <span className="badge" style={{ color: s.color, background: s.bg, borderColor: s.color + "55" }}>
      {severity}
    </span>
  );
}

export function ResultBadge({ result }: { result: ResultStatus }) {
  const map: Record<ResultStatus, { color: string; bg: string }> = {
    PASS: { color: "var(--res-pass)", bg: "var(--res-pass-bg)" },
    FAIL: { color: "var(--res-fail)", bg: "var(--res-fail-bg)" },
    REVIEW: { color: "var(--res-review)", bg: "var(--res-review-bg)" },
    ERROR: { color: "var(--res-error)", bg: "var(--res-error-bg)" },
  };
  const s = map[result];
  return (
    <span className="badge" style={{ color: s.color, background: s.bg, borderColor: s.color + "55" }}>
      {result}
    </span>
  );
}

export function FindingStatusBadge({ status }: { status: FindingStatus }) {
  const map: Record<FindingStatus, { color: string; bg: string; label: string }> = {
    OPEN: { color: "var(--res-fail)", bg: "var(--res-fail-bg)", label: "Open" },
    IN_PROGRESS: { color: "var(--sev-medium)", bg: "var(--sev-medium-bg)", label: "In Progress" },
    RESOLVED: { color: "var(--res-pass)", bg: "var(--res-pass-bg)", label: "Resolved" },
    ACCEPT_RISK: { color: "var(--color-text-muted)", bg: "var(--color-bg-hover)", label: "Accepted Risk" },
  };
  const s = map[status];
  return (
    <span className="badge" style={{ color: s.color, background: s.bg, borderColor: s.color + "55" }}>
      {s.label}
    </span>
  );
}

export function AppStatusBadge({ status }: { status: AppStatus }) {
  const map: Record<AppStatus, { color: string; bg: string }> = {
    DRAFT: { color: "var(--color-text-muted)", bg: "var(--color-bg-hover)" },
    ACTIVE: { color: "var(--res-pass)", bg: "var(--res-pass-bg)" },
    ARCHIVED: { color: "var(--color-text-faint)", bg: "var(--color-bg-hover)" },
  };
  const s = map[status];
  return (
    <span className="badge" style={{ color: s.color, background: s.bg, borderColor: s.color + "55" }}>
      {status}
    </span>
  );
}

export function DecisionBadge({
  decision,
  size = "md",
}: {
  decision: ReleaseDecisionEnum;
  size?: "sm" | "md" | "lg";
}) {
  const map: Record<ReleaseDecisionEnum, { color: string; bg: string; border: string; label: string }> = {
    READY: { color: "var(--color-ready)", bg: "var(--color-ready-bg)", border: "var(--color-ready-border)", label: "READY" },
    READY_WITH_CONDITIONS: {
      color: "var(--color-conditions)",
      bg: "var(--color-conditions-bg)",
      border: "var(--color-conditions-border)",
      label: "READY WITH CONDITIONS",
    },
    NOT_READY: {
      color: "var(--color-not-ready)",
      bg: "var(--color-not-ready-bg)",
      border: "var(--color-not-ready-border)",
      label: "NOT READY",
    },
  };
  const s = map[decision];
  const fontSize = size === "lg" ? 20 : size === "sm" ? 12 : 15;
  const padding = size === "lg" ? "12px 22px" : size === "sm" ? "4px 10px" : "8px 16px";
  return (
    <span
      className="decision-badge"
      style={{ color: s.color, background: s.bg, borderColor: s.border, fontSize, padding }}
    >
      <span className="dot" style={{ background: s.color }} />
      {s.label}
    </span>
  );
}
