import { Link, NavLink, Outlet } from "react-router-dom";

export function Layout() {
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
