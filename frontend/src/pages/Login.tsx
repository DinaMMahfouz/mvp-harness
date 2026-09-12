import { useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../lib/AuthContext";

export function Login() {
  const { session, loading, signInWithEmail } = useAuth();
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!loading && session) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;
    setStatus("sending");
    setErrorMessage(null);
    const { error } = await signInWithEmail(email.trim());
    if (error) {
      setStatus("error");
      setErrorMessage(error);
    } else {
      setStatus("sent");
    }
  }

  return (
    <div className="landing" style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
      <div className="hero-visual-card" style={{ maxWidth: 380, width: "100%", margin: "0 20px" }}>
        <div style={{ fontWeight: 750, fontSize: 17, color: "var(--brand-text)", marginBottom: 24 }}>Plumbline</div>

        <h1 style={{ fontSize: 20, fontWeight: 700, color: "var(--brand-text)", marginBottom: 6 }}>Sign in</h1>
        <p style={{ fontSize: 13, color: "var(--brand-text-muted)", marginBottom: 20, lineHeight: 1.5 }}>
          We'll email you a one-time sign-in link — no password to set or remember.
        </p>

        {status === "sent" ? (
          <div className="notice" role="status">
            <span>
              Check <strong>{email}</strong> for a sign-in link. You can close this tab once you click it.
            </span>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label style={{ color: "var(--brand-text-muted)" }}>Email</label>
              <input
                type="email"
                required
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                style={{ background: "var(--brand-bg-elevated)", borderColor: "var(--brand-border)", color: "var(--brand-text)" }}
              />
            </div>
            {status === "error" && errorMessage && (
              <div className="error-state" style={{ marginBottom: 14, fontSize: 12.5 }}>
                {errorMessage}
              </div>
            )}
            <button type="submit" className="btn btn-brand btn-lg" style={{ width: "100%", justifyContent: "center" }} disabled={status === "sending"}>
              {status === "sending" ? "Sending…" : "Send sign-in link"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
