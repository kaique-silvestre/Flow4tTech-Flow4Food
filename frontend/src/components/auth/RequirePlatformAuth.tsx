import { Navigate, Outlet } from "react-router-dom";
import { usePlatformAuthStore } from "@/stores/platformAuthStore";
import { resolveAuthGuard } from "./authGuard";

export function RequirePlatformAuth() {
  const state = usePlatformAuthStore();
  if (!resolveAuthGuard(state)) return <Navigate to="/platform/login" replace />;
  return <Outlet />;
}
