import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { label: "Dashboard", to: "/" },
  { label: "Comandas", to: "/comandas" },
  { label: "Compras", to: "/compras" },
  { label: "Estoque", to: "/estoque" },
  { label: "Histórico", to: "/estoque/movimentos" },
  { label: "Relatórios", to: "/relatorios" },
  { label: "─ Cadastros ─", to: null },
  { label: "Itens", to: "/cadastros/itens" },
  { label: "Categorias", to: "/cadastros/categorias" },
  { label: "Fornecedores", to: "/cadastros/fornecedores" },
  { label: "Garçons", to: "/cadastros/garcons" },
  { label: "Métodos Pgto.", to: "/cadastros/metodos-pagamento" },
  { label: "Configurações", to: "/configuracoes" },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  return (
    <aside
      className={`flex flex-col border-r bg-white transition-all duration-200 ${
        collapsed ? "w-12" : "w-48"
      }`}
    >
      <button
        className="flex h-10 items-center justify-center border-b text-gray-400 hover:text-gray-700 shrink-0"
        onClick={onToggle}
        title={collapsed ? "Expandir menu" : "Colapsar menu"}
      >
        {collapsed ? "›" : "‹"}
      </button>
      <nav className="flex flex-col gap-1 overflow-hidden p-2 pt-2">
        {NAV_ITEMS.map((item) =>
          item.to === null ? (
            collapsed ? null : (
              <span key={item.label} className="px-3 py-1 text-xs text-gray-400 select-none truncate">
                {item.label}
              </span>
            )
          ) : (
            <NavLink
              key={item.to}
              to={item.to}
              end
              title={item.label}
              className={({ isActive }) =>
                `rounded px-3 py-2 text-sm transition-colors truncate ${
                  isActive
                    ? "bg-gray-100 font-medium text-gray-900"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                }`
              }
            >
              {collapsed ? item.label.slice(0, 2) : item.label}
            </NavLink>
          )
        )}
      </nav>
    </aside>
  );
}
