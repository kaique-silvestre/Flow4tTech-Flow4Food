import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";
import { toast } from "@/lib/toast";
import { Menu, CalendarDays, ArrowUpRight, X } from "lucide-react";
import { useActiveAnnouncements, useMarkAnnouncementRead } from "@/features/comunicados/useAnnouncements";
import { ChangePasswordModal } from "@/features/auth/ChangePasswordModal";
import { Announcement, AnnouncementTag, AnnouncementTitle } from "@/components/ui/announcement";
import { Notifications } from "@/components/ui/notifications";
import { useProximosEventos } from "@/features/calendario/useProximosEventos";
import { cn } from "@/lib/utils";

// mesmas cores do CalendarioPage → TIPO_STYLE
const TIPO_STYLE: Record<string, { tag: string; announcement: string; border: string }> = {
  evento: {
    tag:          "bg-blue-100 text-blue-800",
    announcement: "bg-blue-50 text-blue-900",
    border:       "border-blue-200",
  },
  promocao: {
    tag:          "bg-green-100 text-green-800",
    announcement: "bg-green-50 text-green-900",
    border:       "border-green-200",
  },
  conta_pagar: {
    tag:          "bg-red-100 text-red-800",
    announcement: "bg-red-50 text-red-900",
    border:       "border-red-200",
  },
  entrega_insumo: {
    tag:          "bg-yellow-100 text-yellow-800",
    announcement: "bg-yellow-50 text-yellow-900",
    border:       "border-yellow-200",
  },
};
const TIPO_LABEL: Record<string, string> = {
  evento: "Evento", promocao: "Promo", conta_pagar: "Conta", entrega_insumo: "Entrega",
};
const CYCLE_MS = 30_000;

function ProximoEventoBanner() {
  const navigate = useNavigate();
  const { items } = useProximosEventos(5);
  const [idx, setIdx] = useState(0);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    if (items.length <= 1) return;
    const interval = setInterval(() => {
      // fade out
      setVisible(false);
      setTimeout(() => {
        setIdx((prev) => (prev + 1) % items.length);
        setVisible(true);
      }, 300);
    }, CYCLE_MS);
    return () => clearInterval(interval);
  }, [items.length]);

  // reset index when items change (month flip etc.)
  useEffect(() => { setIdx(0); setVisible(true); }, [items]);

  if (!items.length) return null;
  const item = items[idx];
  const style = TIPO_STYLE[item.tipo] ?? TIPO_STYLE.evento;
  const diasLabel =
    item.diasRestantes === 0 ? "hoje"
    : item.diasRestantes === 1 ? "amanhã"
    : `em ${item.diasRestantes}d`;

  return (
    <button
      onClick={() => navigate("/calendario")}
      className="hidden sm:flex items-center"
      aria-label="Ver próximo evento no calendário"
      style={{ transition: "opacity 0.3s ease", opacity: visible ? 1 : 0 }}
    >
      <Announcement
        variant="outline"
        themed
        className={cn("cursor-pointer text-xs", style.announcement, style.border)}
      >
        <AnnouncementTag className={cn("flex items-center gap-1", style.tag)}>
          <CalendarDays size={11} />
          {TIPO_LABEL[item.tipo] ?? item.tipo}
        </AnnouncementTag>
        <AnnouncementTitle className="text-xs max-w-[200px]">
          <span className="truncate opacity-80">{item.descricao}</span>
          <span className="shrink-0 font-semibold">{diasLabel}</span>
          <ArrowUpRight size={12} className="shrink-0 opacity-50" />
        </AnnouncementTitle>
      </Announcement>
    </button>
  );
}

function ComunicadoBanner() {
  const { data: announcements = [] } = useActiveAnnouncements();
  const markRead = useMarkAnnouncementRead();
  const [dismissed, setDismissed] = useState<number[]>([]);

  const visible = announcements.filter((a) => !dismissed.includes(a.id));
  if (visible.length === 0) return null;
  const ann = visible[0];

  function handleDismiss() {
    setDismissed((prev) => [...prev, ann.id]);
    markRead.mutate(ann.id);
  }

  return (
    <div className="flex items-center gap-2 rounded-lg border border-orange-200 bg-orange-50 px-3 py-1 text-xs text-orange-900 max-w-sm">
      <span className="truncate font-medium">{ann.title}</span>
      <button onClick={handleDismiss} aria-label="Fechar comunicado" className="shrink-0 text-orange-600 hover:text-orange-800">
        <X size={12} />
      </button>
    </div>
  );
}

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
        <span className="font-semibold">Flow4Food</span>
      </div>

      <div className="flex items-center gap-2">
        <ComunicadoBanner />
        <ProximoEventoBanner />
      </div>

      <div className="flex items-center gap-1">
        <Notifications />
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
      </div>

      <ChangePasswordModal open={alterarSenhaOpen} onClose={() => setAlterarSenhaOpen(false)} />
    </header>
  );
}
