import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";
import { toast } from "@/lib/toast";

/**
 * Shared logout flow (clear session + toast + redirect to /login), used by
 * both the sidebar footer's "Sair" and the topbar avatar dropdown's "Sair"
 * so the two never drift out of sync.
 */
export function useLogout(): () => void {
  const clearToken = useAuthStore((s) => s.clearToken);
  const navigate = useNavigate();

  return function logout() {
    clearToken();
    toast.success("Sessão encerrada");
    navigate("/login", { replace: true });
  };
}
