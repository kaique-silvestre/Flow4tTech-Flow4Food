import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";

export function RequireAuth() {
  const { token, user, clearToken } = useAuthStore();
  if (!token) return <Navigate to="/login" replace />;
  if (!user) {
    clearToken();
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
