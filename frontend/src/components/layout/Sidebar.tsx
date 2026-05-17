import { useState } from "react";
import { NavLink } from "react-router-dom";
import { useComandasAbertasCount } from "@/features/comandas/useComandas";
import { useInsumoCriticos } from "@/features/estoque/useEstoque";
import { useContasPagarResumo } from "@/features/contas_pagar/useContasPagar";
import {
  LayoutDashboard,
  ClipboardList,
  UtensilsCrossed,
  ShoppingCart,
  Package,
  History,
  BarChart3,
  Tag,
  Truck,
  Users,
  CreditCard,
  Settings,
  Menu,
  BookOpen,
  ChevronDown,
  ChevronRight,
  FlaskConical,
  Wallet,
  type LucideIcon,
} from "lucide-react";

interface SubNavItem {
  label: string;
  to: string;
  icon: LucideIcon;
}

interface NavItem {
  label: string;
  to: string | null;
  icon?: LucideIcon;
  children?: SubNavItem[];
}

const CADASTROS_CHILDREN: SubNavItem[] = [
  { label: "Categorias", to: "/cadastros/categorias", icon: Tag },
  { label: "Insumos", to: "/cadastros/insumos", icon: FlaskConical },
  { label: "Fornecedores", to: "/cadastros/fornecedores", icon: Truck },
  { label: "Garçons", to: "/cadastros/garcons", icon: Users },
  { label: "Métodos Pgto.", to: "/cadastros/metodos-pagamento", icon: CreditCard },
];

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", to: "/", icon: LayoutDashboard },
  { label: "Comandas", to: "/comandas", icon: ClipboardList },
  { label: "Cardápio", to: "/cardapio", icon: UtensilsCrossed },
  { label: "Estoque", to: "/estoque", icon: Package },
  { label: "Movimentos", to: "/estoque/movimentos", icon: History },
  { label: "Compras", to: "/compras", icon: ShoppingCart },
  { label: "Contas a Pagar", to: "/contas-pagar", icon: Wallet },
  { label: "Relatórios", to: "/relatorios", icon: BarChart3 },
  { label: "Cadastros", to: null, icon: BookOpen, children: CADASTROS_CHILDREN },
  { label: "Configurações", to: "/configuracoes", icon: Settings },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
}

export function Sidebar({ collapsed, onToggle, mobileOpen }: SidebarProps) {
  const [cadastrosOpen, setCadastrosOpen] = useState(true);
  const [cadastrosHovered, setCadastrosHovered] = useState(false);
  const { data: countAbertas = 0 } = useComandasAbertasCount();
  const { data: criticos = [] } = useInsumoCriticos();
  const countCriticos = criticos.length;
  const { data: contasResumo } = useContasPagarResumo();
  const countContasUrgentes = (contasResumo?.vencido ?? 0) + (contasResumo?.pendente ?? 0);

  return (
    <aside
      className={`
        fixed inset-y-0 left-0 z-30 flex w-52 flex-col border-r bg-white shadow-xl transition-all duration-200
        ${mobileOpen ? "translate-x-0" : "-translate-x-full"}
        lg:static lg:z-auto lg:shadow-none lg:translate-x-0
        ${collapsed ? "lg:w-14" : "lg:w-52"}
      `}
    >
      <button
        className="hidden h-10 items-center justify-center border-b text-gray-400 hover:text-gray-700 shrink-0 lg:flex"
        onClick={onToggle}
        title={collapsed ? "Expandir menu" : "Colapsar menu"}
      >
        <Menu size={18} />
      </button>
      <nav className="flex flex-col gap-1 overflow-hidden p-2">
        {NAV_ITEMS.map((item) => {
          if (item.children) {
            if (collapsed) {
              return (
                <div
                  key={item.label}
                  className="relative"
                  onMouseEnter={() => setCadastrosHovered(true)}
                  onMouseLeave={() => setCadastrosHovered(false)}
                >
                  <button
                    className="flex w-full items-center justify-center rounded px-2 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                    title={item.label}
                  >
                    {item.icon && <item.icon size={18} className="shrink-0" />}
                  </button>
                  {cadastrosHovered && (
                    <div className="absolute left-full top-0 z-50 ml-1 min-w-40 rounded-md border bg-white py-1 shadow-lg">
                      {item.children.map((child) => (
                        <NavLink
                          key={child.to}
                          to={child.to}
                          end
                          className={({ isActive }) =>
                            `flex items-center gap-2 px-3 py-2 text-sm transition-colors ${
                              isActive
                                ? "bg-gray-100 font-medium text-gray-900"
                                : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                            }`
                          }
                        >
                          <child.icon size={16} className="shrink-0" />
                          <span>{child.label}</span>
                        </NavLink>
                      ))}
                    </div>
                  )}
                </div>
              );
            }

            return (
              <div key={item.label}>
                <button
                  onClick={() => setCadastrosOpen((o) => !o)}
                  className="flex w-full items-center gap-2 rounded px-2 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                >
                  {item.icon && <item.icon size={18} className="shrink-0" />}
                  <span className="flex-1 truncate text-left">{item.label}</span>
                  {cadastrosOpen ? (
                    <ChevronDown size={14} className="shrink-0" />
                  ) : (
                    <ChevronRight size={14} className="shrink-0" />
                  )}
                </button>
                {cadastrosOpen && (
                  <div className="flex flex-col gap-1 pl-4">
                    {item.children.map((child) => (
                      <NavLink
                        key={child.to}
                        to={child.to}
                        end
                        title={child.label}
                        className={({ isActive }) =>
                          `flex items-center gap-2 rounded px-2 py-1.5 text-sm transition-colors ${
                            isActive
                              ? "bg-gray-100 font-medium text-gray-900"
                              : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                          }`
                        }
                      >
                        <child.icon size={16} className="shrink-0" />
                        <span className="truncate">{child.label}</span>
                      </NavLink>
                    ))}
                  </div>
                )}
              </div>
            );
          }

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
              className={({ isActive }) =>
                `relative flex items-center gap-2 rounded px-2 py-2 text-sm transition-colors ${
                  collapsed ? "justify-center" : ""
                } ${
                  isActive
                    ? "bg-gray-100 font-medium text-gray-900"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                }`
              }
            >
              {item.icon && <item.icon size={18} className="shrink-0" />}
              {!collapsed && <span className="truncate">{item.label}</span>}
              {!collapsed && item.to === "/comandas" && countAbertas > 0 && (
                <span className="ml-auto rounded-full bg-amber-500 px-2 py-0.5 text-xs text-white">
                  {countAbertas}
                </span>
              )}
              {collapsed && item.to === "/comandas" && countAbertas > 0 && (
                <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-amber-500" />
              )}
              {!collapsed && item.to === "/estoque" && countCriticos > 0 && (
                <span className="ml-auto rounded-full bg-red-500 px-2 py-0.5 text-xs text-white">
                  {countCriticos}
                </span>
              )}
              {collapsed && item.to === "/estoque" && countCriticos > 0 && (
                <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-red-500" />
              )}
              {!collapsed && item.to === "/contas-pagar" && countContasUrgentes > 0 && (
                <span className="ml-auto rounded-full bg-orange-500 px-2 py-0.5 text-xs text-white">
                  {countContasUrgentes}
                </span>
              )}
              {collapsed && item.to === "/contas-pagar" && countContasUrgentes > 0 && (
                <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-orange-500" />
              )}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
