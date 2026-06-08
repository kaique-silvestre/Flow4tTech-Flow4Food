import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { NavLink, useLocation } from "react-router-dom";
import { useComandasAbertasCount } from "@/features/comandas/useComandas";
import { useInsumoCriticos } from "@/features/estoque/useEstoque";
import { useContasPagarResumo } from "@/features/contas_pagar/useContasPagar";
import { usePermissions } from "@/hooks/usePermission";
import { ChevronRight, Menu } from "lucide-react";
import { NAV_ITEMS, type SubNavItem } from "./navConfig";

/* ---------- component ---------- */

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
}

export function Sidebar({ collapsed, onToggle, mobileOpen }: SidebarProps) {
  const [openGroup, setOpenGroup] = useState<string | null>(null);
  const [flyoutPos, setFlyoutPos] = useState<{ top: number; left: number }>({ top: 0, left: 0 });
  const navRef = useRef<HTMLDivElement>(null);
  const btnRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const location = useLocation();
  const { data: countAbertas = 0 } = useComandasAbertasCount();
  const { data: criticos = [] } = useInsumoCriticos();
  const countCriticos = criticos.length;
  const { data: contasResumo } = useContasPagarResumo();
  const countContasUrgentes = (contasResumo?.vencido ?? 0) + (contasResumo?.pendente ?? 0);
  const permissions = usePermissions();

  const toggleGroup = useCallback((label: string) => {
    setOpenGroup((prev) => {
      if (prev === label) return null;
      const btn = btnRefs.current[label];
      if (btn) {
        const rect = btn.getBoundingClientRect();
        setFlyoutPos({ top: rect.top, left: rect.right + 6 });
      }
      return label;
    });
  }, []);

  // Close flyout on outside click or Escape
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      const target = e.target as HTMLElement;
      if (navRef.current && !navRef.current.contains(target) && !target.closest("[data-sidebar-flyout]")) {
        setOpenGroup(null);
      }
    }
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpenGroup(null);
    }
    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleKey);
    };
  }, []);

  // Close flyout on route change
  useEffect(() => {
    setOpenGroup(null);
  }, [location.pathname]);

  function visibleChildren(children: SubNavItem[]) {
    return children.filter((c) => !c.screen || permissions.includes(c.screen));
  }

  function getGroupBadge(label: string): { count: number; color: string } | null {
    if (label === "Vendas" && countAbertas > 0) return { count: countAbertas, color: "bg-amber-500" };
    if (label === "Estoque" && countCriticos > 0) return { count: countCriticos, color: "bg-red-500" };
    if (label === "Financeiro" && countContasUrgentes > 0) return { count: countContasUrgentes, color: "bg-orange-500" };
    return null;
  }


  const visibleItems = NAV_ITEMS.filter((item) => {
    if (item.screen && !permissions.includes(item.screen)) return false;
    if (item.children) return visibleChildren(item.children).length > 0;
    return true;
  });

  function renderFlyout(children: SubNavItem[], label: string) {
    return createPortal(
      <div
        data-sidebar-flyout
        style={{ top: flyoutPos.top, left: flyoutPos.left, animation: "flyout-in 150ms ease-out" }}
        className="fixed z-[9999] min-w-48 rounded-lg border border-gray-200 bg-white py-1.5 shadow-xl"
      >
        <div className="px-3 pb-1.5 mb-1 border-b border-gray-100">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">{label}</span>
        </div>
        {children.map((child) => (
            <NavLink
              key={child.to}
              to={child.to}
              end
              className="flex items-center gap-2.5 mx-1.5 px-2.5 py-2 rounded-md text-sm transition-colors text-gray-600 hover:bg-gray-50 hover:text-gray-900"
            >
              <child.icon size={16} className="shrink-0" />
              <span>{child.label}</span>
            </NavLink>
        ))}
      </div>,
      document.body,
    );
  }

  return (
    <aside
      className={`
        fixed inset-y-0 left-0 z-40 flex w-52 flex-col border-r border-gray-200 bg-white shadow-xl transition-all duration-200
        ${mobileOpen ? "translate-x-0" : "-translate-x-full"}
        lg:relative lg:z-40 lg:shadow-none lg:translate-x-0
        ${collapsed ? "lg:w-14" : "lg:w-52"}
      `}
    >
      <button
        className="hidden h-12 items-center justify-center border-b border-gray-200 text-gray-400 hover:text-gray-700 hover:bg-gray-50 shrink-0 lg:flex transition-colors"
        onClick={onToggle}
        title={collapsed ? "Expandir menu" : "Colapsar menu"}
      >
        <Menu size={18} />
      </button>

      <nav ref={navRef} className="flex flex-1 flex-col gap-0.5 p-2 overflow-y-auto">
        {visibleItems.map((item) => {
          if (item.children) {
            const children = visibleChildren(item.children);
            const badge = getGroupBadge(item.label);
            const isOpen = openGroup === item.label;

            return (
              <div key={item.label} className="relative">
                <button
                  ref={(el) => { btnRefs.current[item.label] = el; }}
                  onClick={() => toggleGroup(item.label)}
                  className={`group flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm transition-colors duration-150 ${
                    collapsed ? "justify-center" : ""
                  } ${
                    isOpen
                      ? "bg-gray-100 text-gray-900 font-medium"
                      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                  }`}
                  title={item.label}
                >
                  {item.icon && (
                    <item.icon
                      size={18}
                      className={`shrink-0 transition-colors duration-150 ${
                        isOpen ? "text-gray-900" : "text-gray-400 group-hover:text-gray-600"
                      }`}
                    />
                  )}
                  {!collapsed && <span className="flex-1 truncate text-left">{item.label}</span>}
                  {!collapsed && badge && (
                    <span className={`rounded-full ${badge.color} px-1.5 py-0.5 text-[10px] font-semibold leading-none text-white`}>
                      {badge.count}
                    </span>
                  )}
                  {collapsed && badge && (
                    <span className={`absolute top-0.5 right-0.5 h-2 w-2 rounded-full ${badge.color} ring-2 ring-white`} />
                  )}
                  {!collapsed && (
                    <ChevronRight
                      size={14}
                      className={`shrink-0 text-gray-400 transition-transform duration-150 ${
                        isOpen ? "rotate-0" : ""
                      }`}
                    />
                  )}
                </button>
                {isOpen && renderFlyout(children, item.label)}
              </div>
            );
          }

          /* ---- DIRECT LINK ---- */
          if (item.to === null) {
            return collapsed ? null : (
              <span key={item.label} className="px-3 py-1 text-xs text-gray-400 select-none truncate">
                {item.label}
              </span>
            );
          }

          return (
            <NavLink
              key={item.to}
              to={item.to}
              end
              title={item.label}
              className={`group relative flex items-center gap-2 rounded-lg px-2 py-2 text-sm transition-colors text-gray-600 hover:bg-gray-50 hover:text-gray-900 ${
                collapsed ? "justify-center" : ""
              }`}
            >
              {item.icon && (
                <item.icon
                  size={18}
                  className="shrink-0 transition-colors duration-150 text-gray-400 group-hover:text-gray-600"
                />
              )}
              {!collapsed && <span className="truncate">{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
