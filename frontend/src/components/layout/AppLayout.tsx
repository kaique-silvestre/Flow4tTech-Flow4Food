import { useEffect, useRef, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { useInsumoCriticos } from "@/features/estoque/useEstoque";
import { toast } from "@/lib/toast";

const STORAGE_KEY = "sidebar_collapsed";

function getInitialCollapsed(): boolean {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored !== null) return stored === "true";
  return false;
}

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(getInitialCollapsed);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { data: criticos = [] } = useInsumoCriticos();
  const alertedRef = useRef(false);
  const location = useLocation();

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (alertedRef.current || criticos.length === 0) return;
    alertedRef.current = true;
    for (const insumo of criticos) {
      toast.warning(
        `Estoque crítico: ${insumo.nome} — ${Number(insumo.estoque_disponivel).toFixed(3)} ${insumo.unidade_base} restantes`
      );
    }
  }, [criticos]);

  function handleToggle() {
    setCollapsed((c) => {
      const next = !c;
      localStorage.setItem(STORAGE_KEY, String(next));
      return next;
    });
  }

  return (
    <div className="flex h-screen">
      {mobileOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/50 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <Sidebar collapsed={collapsed} onToggle={handleToggle} mobileOpen={mobileOpen} />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar onMenuClick={() => setMobileOpen((o) => !o)} />
        <main className="flex-1 overflow-auto p-4">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
