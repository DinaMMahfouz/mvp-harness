import { Link } from "react-router-dom";
import { DecisionBadge } from "../components/Badges";
import { AuthorizedUseNotice } from "../components/AuthorizedUseNotice";

const FLOW_STEPS = ["Connect", "Break", "Understand", "Fix", "Prove", "Ship"];

const FEATURES = [
  {
    title: "Application Registry",
    description:
      "Register a chatbot, RAG pipeline, agent, MCP server, or workflow. Define exactly what it should do — and what it must never do.",
  },
  {
    title: "Assurance Run + Findings",
    description:
      "Run a real, targeted test plan against the live endpoint. Every finding ships with the exact attack, the exact response, and why it failed.",
  },
  {
    title: "Harden → Retest → Release Decision",
    description:
      "Fix the root cause, then retest the identical prompts. See what's fixed, what remains, and any regressions — and get one clear decision.",
  },
];

export function Home() {
  return (
    <div className="landing">
      <nav className="landing-nav">
        <div className="brand">
          <span className="brand-mark">H</span>
          HARNESS
        </div>
        <div className="landing-nav-links">
          <a href="#how-it-works">How it works</a>
          <a href="#decision">Release decision</a>
          <Link to="/dashboard" className="btn btn-primary btn-sm">
            Open App
          </Link>
        </div>
      </nav>

      <header className="hero">
        <span className="hero-eyebrow">AI Release Assurance</span>
        <h1>
          Your AI works.
          <br />
          But is it <span className="accent">ready to ship?</span>
        </h1>
        <p className="hero-sub">
          Test your AI application against adversarial conditions, understand exactly what can fail, harden it,
          retest the same weaknesses, and get a clear release-readiness decision. Not another vulnerability count —
          one answer: ready, or not.
        </p>
        <div className="hero-cta-row">
          <Link to="/applications/new" className="btn btn-primary btn-lg">
            Run Assurance
          </Link>
          <Link to="/dashboard" className="btn btn-lg">
            View Demo
          </Link>
        </div>

        <div className="flow-strip" aria-label="HARNESS workflow">
          {FLOW_STEPS.map((step, i) => (
            <span key={step} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span className="flow-step">
                <span className="flow-num">{i + 1}</span>
                {step}
              </span>
              {i < FLOW_STEPS.length - 1 && (
                <span className="flow-arrow" aria-hidden="true">
                  →
                </span>
              )}
            </span>
          ))}
        </div>
      </header>

      <section className="landing-section tight">
        <div style={{ maxWidth: 640, margin: "0 auto" }}>
          <AuthorizedUseNotice />
        </div>
      </section>

      <section className="landing-section" id="how-it-works">
        <div className="section-eyebrow">The core loop</div>
        <h2 className="section-heading">Three features. One decision.</h2>
        <p className="section-sub">
          HARNESS is intentionally narrow. Everything else — email alerts, the Excel issue register, n8n automation
          — supports this loop. None of it decides anything on its own.
        </p>
        <div className="feature-grid">
          {FEATURES.map((f, i) => (
            <div className="feature-card" key={f.title}>
              <div className="feature-num">{i + 1}</div>
              <h3>{f.title}</h3>
              <p>{f.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="landing-section" id="decision">
        <div className="section-eyebrow">The final product</div>
        <h2 className="section-heading">A release decision you can defend</h2>
        <p className="section-sub">
          Every important conclusion shows the attack, the exact response, why it failed, and the recommended fix —
          no mysterious security score standing alone.
        </p>
        <div className="decision-showcase">
          <div className="decision-card" style={{ borderColor: "var(--color-not-ready-border)", background: "var(--color-not-ready-bg)" }}>
            <DecisionBadge decision="NOT_READY" size="sm" />
            <h4>1 CRITICAL prompt-injection failure</h4>
            <p>Blocks release until the trusted-instruction boundary is fixed and retested.</p>
          </div>
          <div className="decision-card" style={{ borderColor: "var(--color-conditions-border)", background: "var(--color-conditions-bg)" }}>
            <DecisionBadge decision="READY_WITH_CONDITIONS" size="sm" />
            <h4>8 fixed, 0 regressions, 2 risks accepted</h4>
            <p>Ship with documented, explicitly accepted low-severity conditions.</p>
          </div>
          <div className="decision-card" style={{ borderColor: "var(--color-ready-border)", background: "var(--color-ready-bg)" }}>
            <DecisionBadge decision="READY" size="sm" />
            <h4>All required categories passed</h4>
            <p>No blocking findings. No regressions from the last hardening pass.</p>
          </div>
        </div>
      </section>

      <section className="landing-section tight" style={{ textAlign: "center" }}>
        <h2 className="section-heading">Break it before your users do.</h2>
        <p className="section-sub">Register your first application and see a real release decision in minutes.</p>
        <div className="hero-cta-row" style={{ marginBottom: 0 }}>
          <Link to="/applications/new" className="btn btn-primary btn-lg">
            Run Assurance
          </Link>
        </div>
      </section>

      <footer className="landing-footer">
        <p className="muted">HARNESS — AI Release Assurance. For AI applications you own or are authorized to test.</p>
      </footer>
    </div>
  );
}
