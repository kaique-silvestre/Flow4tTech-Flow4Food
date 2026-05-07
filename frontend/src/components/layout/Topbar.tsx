import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/authStore";

export function Topbar() {
  const clearToken = useAuthStore((s) => s.clearToken);
  const navigate = useNavigate();

  function handleLogout() {
    clearToken();
    navigate("/login", { replace: true });
  }

  return (
    <header className="flex h-12 items-center justify-between border-b bg-white px-4">
      <span className="font-semibold">Matchpoint</span>
      <Button variant="ghost" size="sm" onClick={handleLogout}>
        Sair
      </Button>
    </header>
  );
}
