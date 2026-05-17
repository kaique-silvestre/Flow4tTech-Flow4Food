import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/authStore";
import { toast } from "@/lib/toast";

export function Topbar() {
  const clearToken = useAuthStore((s) => s.clearToken);
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();

  function handleLogout() {
    clearToken();
    toast.success("Sessão encerrada");
    navigate("/login", { replace: true });
  }

  return (
    <header className="flex h-12 items-center justify-between border-b bg-white px-4">
      <span className="font-semibold">Flow4Tech</span>
      <div className="flex items-center gap-3">
        {user && (
          <div className="text-right">
            <p className="text-sm font-medium text-gray-800">{user.name || user.username}</p>
            <p className="text-xs text-gray-400">{user.profile_name}</p>
          </div>
        )}
        <Button variant="ghost" size="sm" onClick={handleLogout}>
          Sair
        </Button>
      </div>
    </header>
  );
}
