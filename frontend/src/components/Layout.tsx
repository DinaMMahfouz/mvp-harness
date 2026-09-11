import { NavLink, Outlet } from "react-router-dom";

export function Layout() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">H</span>
          HARNESS
        </div>
        <NavLink to="/" end className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
          Dashboard
        </NavLink>
        <NavLink to="/applications" className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
          Applications
        </NavLink>
        <div style={{ marginTop: "auto", padding: "10px", fontSize: 11.5, color: "var(--color-text-faint)" }}>
          AI Release Assurance
        </div>
      </aside>
      <div className="main-content">
        <Outlet />
      </div>
    </div>
  );
}
