import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/authStore";
import { toast } from "@/lib/toast";
import { ChangePasswordModal } from "@/features/auth/ChangePasswordModal";

export function Topbar() {
  const clearToken = useAuthStore((s) => s.clearToken);
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  const [changePwdOpen, setChangePwdOpen] = useState(false);

  function handleLogout() {
    clearToken();
    toast.success("Sessão encerrada");
    navigate("/login", { replace: true });
  }

  return (
    <>
      <header className="flex h-12 items-center justify-between border-b bg-white px-4">
        <span className="font-semibold">Flow4Tech</span>
        <div className="flex items-center gap-3">
          {user && (
            <span className="text-sm text-gray-500">
              {user.name || user.username}
              <span className="ml-1 text-xs text-gray-400">({user.profile_name})</span>
            </span>
          )}
          <Button variant="ghost" size="sm" onClick={() => setChangePwdOpen(true)}>
            Alterar senha
          </Button>
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            Sair
          </Button>
        </div>
      </header>
      <ChangePasswordModal open={changePwdOpen} onClose={() => setChangePwdOpen(false)} />
    </>
  );
}
