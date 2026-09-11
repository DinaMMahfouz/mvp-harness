import { Link } from "react-router-dom";

export function NotFound() {
  return (
    <div className="empty-state">
      <p style={{ fontWeight: 650, color: "var(--color-text)", marginBottom: 6 }}>Page not found</p>
      <p style={{ marginBottom: 14 }}>The page you're looking for doesn't exist.</p>
      <Link to="/" className="btn btn-primary">
        Back to Dashboard
      </Link>
    </div>
  );
}
