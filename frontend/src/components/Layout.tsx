import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/AuthContext";

export function Layout() {
  const { user, profile, signOut } = useAuth();
  const navigate = useNavigate();

  async function handleSignOut() {
    await signOut();
    navigate("/login", { replace: true });
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link to="/" className="brand" style={{ color: "inherit" }} aria-label="Plumbline home">
          Plumbline
        </Link>
        <NavLink to="/dashboard" className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
          Dashboard
        </NavLink>
        <NavLink to="/applications" className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
          Applications
        </NavLink>
        <div style={{ marginTop: "auto", padding: "10px 10px 0" }}>
          {user && (
            <div style={{ padding: "8px 10px", marginBottom: 8, borderTop: "1px solid var(--color-border-subtle)", paddingTop: 12 }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
                <span
                  style={{ fontSize: 12, color: "var(--color-text)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                  title={user.email}
                >
                  {user.email}
                </span>
                {profile?.role === "admin" && (
                  <span className="badge" style={{ color: "var(--color-accent)", background: "var(--color-accent-bg)", flexShrink: 0 }}>
                    Admin
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={handleSignOut}
                className="btn btn-sm"
                style={{ marginTop: 8, width: "100%", justifyContent: "center" }}
              >
                Sign out
              </button>
            </div>
          )}
          <div style={{ fontSize: 11.5, color: "var(--color-text-faint)", marginBottom: 8 }}>
            AI Release Assurance
          </div>
          <div style={{ fontSize: 10.5, lineHeight: 1.5, color: "var(--color-text-faint)" }}>
            For apps you own or are authorized to test.
          </div>
        </div>
      </aside>
      <div className="main-content">
        <Outlet />
      </div>
    </div>
  );
}
