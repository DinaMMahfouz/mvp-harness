import { Link } from "react-router-dom";
import { AuthorizedUseNotice } from "../components/AuthorizedUseNotice";

const FLOW_STEPS = ["Connect", "Break", "Understand", "Fix", "Prove", "Ship"];

const INTEGRATIONS = ["Claude", "Supabase", "n8n", "GitHub"];

const FEATURES = [
  {
    icon: <ShieldIcon />,
    title: "Application Registry",
    description:
      "Register a chatbot, RAG pipeline, agent, MCP server, or workflow. Define exactly what it should do — and what it must never do.",
  },
  {
    icon: <TargetIcon />,
    title: "Assurance Run + Findings",
    description:
      "Run a real, targeted test plan against the live endpoint. Every finding ships with the exact attack, the exact response, and why it failed.",
  },
  {
    icon: <RefreshIcon />,
    title: "Harden → Retest → Release Decision",
    description:
      "Fix the root cause, then retest the identical prompts. See what's fixed, what remains, and any regressions — and get one clear decision.",
  },
];

const STATS = [
  { value: "7", label: "Adversarial test categories" },
  { value: "5", label: "Supported app types" },
  { value: "3", label: "Steps: run, harden, retest" },
  { value: "100%", label: "Findings backed by evidence" },
];

function ShieldIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 3 4.5 5.5V11c0 5 3.2 8.6 7.5 10 4.3-1.4 7.5-5 7.5-10V5.5L12 3Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
      <path d="M9 12.2 11.2 14.4 15.4 9.8" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function TargetIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="8.2" stroke="currentColor" strokeWidth="1.7" />
      <circle cx="12" cy="12" r="4.4" stroke="currentColor" strokeWidth="1.7" />
      <circle cx="12" cy="12" r="0.9" fill="currentColor" />
    </svg>
  );
}

function RefreshIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4.5 12a7.5 7.5 0 0 1 12.6-5.5M19.5 12a7.5 7.5 0 0 1-12.6 5.5"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
      <path d="M17.5 3.5v3.5H14M6.5 20.5V17H10" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function Home() {
  return (
    <div className="landing">
      <nav className="landing-nav">
        <div className="brand">
          Plumbline
        </div>
        <div className="landing-nav-links">
          <a href="#how-it-works">How it works</a>
          <a href="#decision">Release decision</a>
          <Link to="/dashboard" className="btn btn-brand btn-sm">
            Open App
          </Link>
        </div>
      </nav>

      <header className="hero-grid">
        <div>
          <span className="hero-eyebrow">AI Release Assurance</span>
          <h1>
            Your AI works.
            <br />
            But is it <span className="accent">ready to ship?</span>
          </h1>
          <p className="hero-sub">
            Test your AI application against adversarial conditions, understand exactly what can fail, harden it,
            retest the same weaknesses, and get a clear release-readiness decision. Not another vulnerability count
            — one answer: ready, or not.
          </p>
          <div className="hero-cta-row">
            <Link to="/applications/new" className="btn btn-brand btn-lg">
              Run Assurance
            </Link>
            <Link to="/dashboard" className="btn btn-ghost-brand btn-lg">
              View Demo
            </Link>
          </div>
          <div className="integrations-row">
            <span className="integrations-label">Built on</span>
            <div className="integrations-list">
              {INTEGRATIONS.map((name) => (
                <span className="integration-chip" key={name}>
                  {name}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="hero-visual">
          <div className="hero-visual-card">
            <div className="hvc-head">
              <span className="hvc-title">Release Decision</span>
              <span className="hvc-dot" aria-hidden="true" />
            </div>
            <div className="hvc-score">READY</div>
            <div className="hvc-score-label">with conditions · assurance score 87</div>
            <div className="hvc-row">
              <span className="hvc-label">Blocking findings</span>
              <span className="hvc-val">0</span>
            </div>
            <div className="hvc-row">
              <span className="hvc-label">Fixed since last run</span>
              <span className="hvc-val">8</span>
            </div>
            <div className="hvc-row">
              <span className="hvc-label">Regressions</span>
              <span className="hvc-val">0</span>
            </div>
          </div>
          <div className="hero-float-card">
            <span className="hfc-icon">
              <ShieldIcon />
            </span>
            <span>
              <div className="hfc-title">Categories covered</div>
              <div className="hfc-val">7 / 7</div>
            </span>
          </div>
        </div>
      </header>

      <div className="landing-section tight" style={{ paddingTop: 0 }}>
        <div style={{ maxWidth: 640, margin: "0 auto" }}>
          <AuthorizedUseNotice />
        </div>
      </div>

      <section className="landing-section" style={{ paddingTop: 0, paddingBottom: 40 }} aria-label="Plumbline workflow">
        <div className="flow-strip" style={{ justifyContent: "center" }}>
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
      </section>

      <section className="landing-section" id="how-it-works" style={{ paddingTop: 40 }}>
        <div className="section-eyebrow">The core loop</div>
        <h2 className="section-heading">Three features. One decision.</h2>
        <p className="section-sub">
          Plumbline is intentionally narrow. Everything else — email alerts, the Excel issue register, n8n automation
          — supports this loop. None of it decides anything on its own.
        </p>
        <div className="feature-grid">
          {FEATURES.map((f) => (
            <div className="feature-card" key={f.title}>
              <div className="feature-icon">{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="landing-section" style={{ paddingTop: 0 }}>
        <div className="landing-stats">
          {STATS.map((s) => (
            <div className="landing-stat" key={s.label}>
              <div className="ls-value">{s.value}</div>
              <div className="ls-label">{s.label}</div>
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
          <div className="decision-card" style={{ borderColor: "rgba(239,68,68,0.35)" }}>
            <span className="decision-badge" style={{ color: "#ef4444", background: "rgba(239,68,68,0.14)", borderColor: "rgba(239,68,68,0.4)" }}>
              <span className="dot" style={{ background: "#ef4444" }} />
              NOT READY
            </span>
            <h4>1 CRITICAL prompt-injection failure</h4>
            <p>Blocks release until the trusted-instruction boundary is fixed and retested.</p>
          </div>
          <div className="decision-card" style={{ borderColor: "rgba(240,180,41,0.35)" }}>
            <span className="decision-badge" style={{ color: "#f0b429", background: "rgba(240,180,41,0.14)", borderColor: "rgba(240,180,41,0.4)" }}>
              <span className="dot" style={{ background: "#f0b429" }} />
              READY WITH CONDITIONS
            </span>
            <h4>8 fixed, 0 regressions, 2 risks accepted</h4>
            <p>Ship with documented, explicitly accepted low-severity conditions.</p>
          </div>
          <div className="decision-card" style={{ borderColor: "rgba(34,197,94,0.35)" }}>
            <span className="decision-badge" style={{ color: "#22c55e", background: "rgba(34,197,94,0.14)", borderColor: "rgba(34,197,94,0.4)" }}>
              <span className="dot" style={{ background: "#22c55e" }} />
              READY
            </span>
            <h4>All required categories passed</h4>
            <p>No blocking findings. No regressions from the last hardening pass.</p>
          </div>
        </div>
      </section>

      <section className="landing-section" style={{ paddingTop: 20 }}>
        <div className="cta-banner">
          <div>
            <h2>Break it before your users do.</h2>
            <p>Register your first application and see a real release decision in minutes.</p>
          </div>
          <div className="cta-banner-form">
            <input type="text" placeholder="https://your-app-endpoint.com" aria-label="Your application endpoint" readOnly />
            <Link to="/applications/new" className="btn btn-lg">
              Run Assurance →
            </Link>
          </div>
        </div>
      </section>

      <footer className="landing-footer">
        <div className="landing-footer-grid">
          <div className="landing-footer-brand">
            <div className="brand">
              Plumbline
            </div>
            <p>AI Release Assurance. For AI applications you own or are authorized to test.</p>
          </div>
          <div className="footer-col">
            <div className="footer-col-title">Product</div>
            <Link to="/dashboard">Dashboard</Link>
            <Link to="/applications">Applications</Link>
            <Link to="/applications/new">Run Assurance</Link>
            <a href="#decision">Release Decision</a>
          </div>
          <div className="footer-col">
            <div className="footer-col-title">Resources</div>
            <a href="#how-it-works">How it works</a>
            <a href="https://github.com/DinaMMahfouz/mvp-harness" target="_blank" rel="noreferrer">
              GitHub
            </a>
          </div>
          <div className="footer-col">
            <div className="footer-col-title">Company</div>
            <span style={{ color: "var(--color-text-muted)", fontSize: 13 }}>Built with Claude Code</span>
          </div>
        </div>
        <div className="landing-footer-bottom">
          <p className="muted">© 2026 Plumbline. AI Release Assurance.</p>
          <p className="muted">For AI applications you own or are authorized to test.</p>
        </div>
      </footer>
    </div>
  );
}
