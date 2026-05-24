import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";
import { toast } from "@/lib/toast";
import { Menu } from "lucide-react";
import { ChangePasswordModal } from "@/features/auth/ChangePasswordModal";

function getInitials(name?: string, username?: string): string {
  const target = name || username || "?";
  return target
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
}

interface TopbarProps {
  onMenuClick: () => void;
}

export function Topbar({ onMenuClick }: TopbarProps) {
  const clearToken = useAuthStore((s) => s.clearToken);
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [alterarSenhaOpen, setAlterarSenhaOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  function handleLogout() {
    setOpen(false);
    clearToken();
    toast.success("Sessão encerrada");
    navigate("/login", { replace: true });
  }

  function handleAlterarSenha() {
    setOpen(false);
    setAlterarSenhaOpen(true);
  }

  const initials = getInitials(user?.name, user?.username);

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
        <span className="font-semibold">Flow4Tech</span>
      </div>

      <div className="relative" ref={menuRef}>
        <button
          onClick={() => setOpen((v) => !v)}
          className="flex items-center gap-2.5 rounded-lg px-2 py-1.5 hover:bg-gray-100 transition-colors"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-900 text-white text-xs font-semibold select-none shrink-0">
            {initials}
          </div>
          {user && (
            <div className="text-left hidden sm:block">
              <p className="text-sm font-medium text-gray-800 leading-tight">{user.name || user.username}</p>
              <p className="text-xs text-gray-400 leading-tight">{user.profile_name}</p>
            </div>
          )}
          <svg
            className={`h-3.5 w-3.5 text-gray-400 transition-transform ${open ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {open && (
          <div className="absolute right-0 top-full mt-1.5 w-56 rounded-lg border bg-white shadow-lg z-50 overflow-hidden">
            <div className="flex items-center gap-3 px-4 py-3 border-b bg-gray-50">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gray-900 text-white text-sm font-semibold select-none shrink-0">
                {initials}
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-gray-900 truncate">{user?.name || user?.username}</p>
                <p className="text-xs text-gray-500 truncate">{user?.profile_name}</p>
              </div>
            </div>
            <div className="py-1">
              <button
                className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                onClick={handleAlterarSenha}
              >
                Alterar Senha
              </button>
              <div className="my-1 border-t" />
              <button
                className="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors"
                onClick={handleLogout}
              >
                Sair
              </button>
            </div>
          </div>
        )}
      </div>

      <ChangePasswordModal open={alterarSenhaOpen} onClose={() => setAlterarSenhaOpen(false)} />
    </header>
  );
}
