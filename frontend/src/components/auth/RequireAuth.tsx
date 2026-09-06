import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";
import { IMPERSONATION_SESSION_KEY } from "@/lib/impersonation";
import { resolveAuthGuard } from "./authGuard";

export function RequireAuth() {
  const state = useAuthStore();
  const hasImpersonation = sessionStorage.getItem(IMPERSONATION_SESSION_KEY) !== null;

  if (!resolveAuthGuard(state, hasImpersonation)) return <Navigate to="/login" replace />;
  return <Outlet />;
}
