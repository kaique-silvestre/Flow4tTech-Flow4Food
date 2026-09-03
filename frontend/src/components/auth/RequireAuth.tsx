import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";
import { IMPERSONATION_SESSION_KEY } from "@/lib/impersonation";

export function RequireAuth() {
  const { token, user, clearToken } = useAuthStore();
  const impersonationToken = sessionStorage.getItem(IMPERSONATION_SESSION_KEY);

  if (!token && !impersonationToken) return <Navigate to="/login" replace />;
  if (!user && !impersonationToken) {
    clearToken();
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
