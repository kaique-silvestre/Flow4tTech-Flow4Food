import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/authStore";
import { Menu } from "lucide-react";

interface TopbarProps {
  onMenuClick: () => void;
}

export function Topbar({ onMenuClick }: TopbarProps) {
  const clearToken = useAuthStore((s) => s.clearToken);
  const navigate = useNavigate();

  function handleLogout() {
    clearToken();
    navigate("/login", { replace: true });
  }

  return (
    <header className="flex h-12 items-center justify-between border-b bg-white px-4">
      <div className="flex items-center gap-2">
        <button
          className="flex items-center justify-center rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-700 lg:hidden"
          onClick={onMenuClick}
          aria-label="Abrir menu"
        >
          <Menu size={20} />
        </button>
        <span className="font-semibold">Matchpoint</span>
      </div>
      <Button variant="ghost" size="sm" onClick={handleLogout}>
        Sair
      </Button>
    </header>
  );
}
