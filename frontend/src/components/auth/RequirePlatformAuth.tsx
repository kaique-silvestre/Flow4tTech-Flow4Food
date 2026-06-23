import { Navigate, Outlet } from "react-router-dom";
import { usePlatformAuthStore } from "@/stores/platformAuthStore";

export function RequirePlatformAuth() {
  const { token, user, clearToken } = usePlatformAuthStore();
  if (!token) return <Navigate to="/platform/login" replace />;
  if (!user) {
    clearToken();
    return <Navigate to="/platform/login" replace />;
  }
  return <Outlet />;
}
