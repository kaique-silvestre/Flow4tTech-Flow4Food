import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { NavLink, useLocation } from "react-router-dom";
import { useComandasAbertasCount } from "@/features/comandas/useComandas";
import { useInsumoCriticos } from "@/features/estoque/useEstoque";
import { useContasPagarResumo } from "@/features/contas_pagar/useContasPagar";
import { usePermissions } from "@/hooks/usePermission";
import { useFeatureFlags } from "@/hooks/useFeatureFlags";
import { ChevronRight, Menu, Search } from "lucide-react";
import { NAV_GROUPS, filterNavItems, type NavItem, type SubNavItem } from "./navConfig";
import { NavBadge } from "@/components/ui/nav-badge";
import { useAuthStore } from "@/stores/authStore";
import { SUBSCRIPTION_STATUS_LABELS } from "@/features/platform/subscriptionStatus";

/* ---------- Bloco Empresa ---------- */

/** Bloco estático (não-clicável) com a identidade da empresa (tenant) logada:
 * quadrado com a inicial, nome completo e status da assinatura como subtítulo.
 * Tolerante a token sem `tenant_name`/`subscription_status` (ex: token emitido
 * antes da ticket 01) — nesse caso mostra só o que estiver disponível. */
function EmpresaBlock({ collapsed }: { collapsed: boolean }) {
  const user = useAuthStore((s) => s.user);
  if (!user) return null;

  const tenantName = user.tenant_name;
  const statusLabel = user.subscription_status
    ? (SUBSCRIPTION_STATUS_LABELS[user.subscription_status] ?? user.subscription_status)
    : null;

  if (!tenantName && !statusLabel) return null;

  const initial = tenantName ? tenantName.charAt(0).toUpperCase() : "?";

  return (
    <div
      className={`flex items-center gap-2.5 border-b border-gray-200 px-3 py-3 shrink-0 ${
        collapsed ? "justify-center px-2" : ""
      }`}
      title={collapsed ? tenantName : undefined}
    >
      <div className="flex h-9 w-9 items-center justify-center rounded-md bg-gray-900 text-white text-sm font-semibold select-none shrink-0">
        {initial}
      </div>
      {!collapsed && (tenantName || statusLabel) && (
        <div className="min-w-0">
          {tenantName && (
            <p className="text-sm font-semibold text-gray-900 truncate" title={tenantName}>
              {tenantName}
            </p>
          )}
          {statusLabel && <p className="text-xs text-gray-400 truncate">{statusLabel}</p>}
        </div>
      )}
    </div>
  );
}

/* ---------- component ---------- */

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
}

export function Sidebar({ collapsed, onToggle, mobileOpen }: SidebarProps) {
  const [openGroup, setOpenGroup] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
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
  const featureFlags = useFeatureFlags();

  const isFeatureEnabled = (feature?: string) => {
    if (!feature) return true;
    if (!(feature in featureFlags)) return true;
    return featureFlags[feature];
  };

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

  // Keep the flyout anchored to its trigger button if the sidebar is
  // collapsed/expanded while a group is open (e.g. user toggles collapse
  // without closing the open group first) — recomputes the portal position
  // against the current (icon-only) button rect.
  useEffect(() => {
    if (!collapsed || !openGroup) return;
    const btn = btnRefs.current[openGroup];
    if (btn) {
      const rect = btn.getBoundingClientRect();
      setFlyoutPos({ top: rect.top, left: rect.right + 6 });
    }
  }, [collapsed, openGroup]);

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
    return children.filter(
      (c) =>
        (!c.screen || permissions.includes(c.screen)) &&
        isFeatureEnabled(c.feature),
    );
  }

  function getGroupBadge(label: string): { count: number; color: string } | null {
    if (label === "Vendas" && countAbertas > 0) return { count: countAbertas, color: "bg-amber-500" };
    if (label === "Estoque" && countCriticos > 0) return { count: countCriticos, color: "bg-red-500" };
    if (label === "Financeiro" && countContasUrgentes > 0) return { count: countContasUrgentes, color: "bg-orange-500" };
    return null;
  }


  function visibleItemsOf(items: NavItem[]) {
    return items.filter((item) => {
      if (item.screen && !permissions.includes(item.screen)) return false;
      if (!isFeatureEnabled(item.feature)) return false;
      if (item.children) return visibleChildren(item.children).length > 0;
      return true;
    });
  }

  const visibleGroups = NAV_GROUPS.map((group) => ({
    heading: group.heading,
    items: visibleItemsOf(group.items),
  })).filter((group) => group.items.length > 0);

  // Search filters on top of what's already visible by permission/feature —
  // it never re-introduces an item the user isn't allowed to see.
  const filteredGroups = filterNavItems(searchQuery, visibleGroups);

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

      <EmpresaBlock collapsed={collapsed} />

      {/* Colapsada: campo some inteiramente (sem espaço pra digitar/exibir
          texto). O valor digitado fica preservado em `searchQuery` mesmo
          escondido, e reaparece ao expandir de novo. */}
      {!collapsed && (
        <div className="border-b border-gray-200 px-3 py-2 shrink-0">
          <div className="relative">
            <Search
              size={14}
              className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400"
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar no menu..."
              aria-label="Buscar no menu"
              className="w-full rounded-md border border-gray-200 bg-gray-50 py-1.5 pl-8 pr-2.5 text-sm text-gray-700 placeholder:text-gray-400 focus:border-gray-300 focus:bg-white focus:outline-none"
            />
          </div>
        </div>
      )}

      <nav ref={navRef} className="flex flex-1 flex-col gap-0.5 p-2 overflow-y-auto">
        {filteredGroups.map((group, groupIndex) => (
          <div key={group.heading ?? `group-${groupIndex}`} className="flex flex-col gap-0.5">
            {group.heading && !collapsed && (
              <span className="px-3 pt-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-gray-400 select-none truncate">
                {group.heading}
              </span>
            )}
            {group.items.map((item) => {
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
                    <NavBadge count={badge.count} color={badge.color} />
                  )}
                  {collapsed && badge && (
                    <NavBadge count={badge.count} color={badge.color} dot />
                  )}
                  {!collapsed && (
                    <ChevronRight
                      size={14}
                      className={`shrink-0 text-gray-400 transition-transform duration-150 ${
                        isOpen ? "rotate-90" : "rotate-0"
                      }`}
                    />
                  )}
                </button>

                {/* Expandida: accordion inline embaixo do grupo (CSS grid
                    grid-rows-[0fr]->[1fr] anima a altura sem cortar o
                    conteúdo com overflow fixo). Colapsada: flyout via
                    portal, comportamento inalterado. */}
                {!collapsed && (
                  <div
                    className={`grid transition-[grid-template-rows] duration-200 ease-in-out ${
                      isOpen ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
                    }`}
                  >
                    <div className="overflow-hidden">
                      <div className="flex flex-col gap-0.5 py-0.5">
                        {children.map((child) => (
                          <NavLink
                            key={child.to}
                            to={child.to}
                            end
                            className="flex items-center gap-2.5 rounded-md py-2 pl-9 pr-2.5 text-sm transition-colors text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                          >
                            <child.icon size={16} className="shrink-0" />
                            <span className="truncate">{child.label}</span>
                          </NavLink>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
                {collapsed && isOpen && renderFlyout(children, item.label)}
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
          </div>
        ))}
      </nav>
    </aside>
  );
}
