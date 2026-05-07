import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { label: "Dashboard", to: "/" },
  { label: "Comandas", to: "/comandas" },
  { label: "Estoque", to: "/estoque" },
  { label: "Compras", to: "/compras" },
  { label: "Relatórios", to: "/relatorios" },
  { label: "Configurações", to: "/configuracoes" },
];

export function Sidebar() {
  return (
    <aside className="flex w-48 flex-col border-r bg-white">
      <nav className="flex flex-col gap-1 p-2 pt-4">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              `rounded px-3 py-2 text-sm transition-colors ${
                isActive
                  ? "bg-gray-100 font-medium text-gray-900"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
