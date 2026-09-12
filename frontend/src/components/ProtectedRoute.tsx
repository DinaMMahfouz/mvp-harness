import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../lib/AuthContext";
import { Loading } from "./States";

export function ProtectedRoute() {
  const { session, loading } = useAuth();

  if (loading) return <Loading label="Checking your session…" />;
  if (!session) return <Navigate to="/login" replace />;

  return <Outlet />;
}
