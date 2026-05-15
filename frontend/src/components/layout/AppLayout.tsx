import { useEffect, useRef, useState } from "react";
import { Outlet } from "react-router-dom";
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
  const { data: criticos = [] } = useInsumoCriticos();
  const alertedRef = useRef(false);

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
      <Sidebar collapsed={collapsed} onToggle={handleToggle} />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-auto p-4">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
