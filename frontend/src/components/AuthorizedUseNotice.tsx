function WarningIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true" style={{ flexShrink: 0, marginTop: 1 }}>
      <path
        d="M12 3.5 21.5 20h-19L12 3.5Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path d="M12 9.5v5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <circle cx="12" cy="17.2" r="0.9" fill="currentColor" />
    </svg>
  );
}

export function AuthorizedUseNotice({ compact = false }: { compact?: boolean }) {
  return (
    <div className={"notice" + (compact ? " notice-compact" : "")} role="note">
      <span style={{ color: "var(--color-conditions)" }}>
        <WarningIcon />
      </span>
      <span>
        <strong>Authorized use only.</strong> HARNESS is for testing AI applications you own or are explicitly
        authorized to test. It performs controlled assurance probes, not destructive exploitation.
      </span>
    </div>
  );
}
