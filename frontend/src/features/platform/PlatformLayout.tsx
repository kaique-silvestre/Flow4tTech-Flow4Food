import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { usePlatformAuthStore } from "@/stores/platformAuthStore";
import { Building2, LayoutDashboard, Megaphone, ShieldCheck, Menu, X } from "lucide-react";

const NAV_ITEMS = [
  { label: "Empresas", to: "/platform/tenants", icon: Building2 },
  { label: "Cockpit", to: "/platform/cockpit", icon: LayoutDashboard },
  { label: "Comunicados", to: "/platform/announcements", icon: Megaphone },
  { label: "Auditoria", to: "/platform/audit", icon: ShieldCheck },
] as const;

export function PlatformLayout() {
  const { user, clearToken } = usePlatformAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  function handleLogout() {
    clearToken();
    void navigate("/platform/login");
  }

  return (
    <div className="flex h-screen">
      {/* mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/50 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* sidebar */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-40 flex w-52 flex-col border-r border-gray-200 bg-white shadow-xl transition-transform duration-200
          ${mobileOpen ? "translate-x-0" : "-translate-x-full"}
          lg:relative lg:z-auto lg:w-52 lg:shadow-none lg:translate-x-0
        `}
      >
        {/* sidebar header */}
        <div className="flex h-12 items-center justify-between border-b border-gray-200 px-4 shrink-0">
          <span className="text-sm font-bold text-gray-900 truncate">Flow4Tech Admin</span>
          <button
            className="lg:hidden text-gray-400 hover:text-gray-700"
            onClick={() => setMobileOpen(false)}
          >
            <X size={18} />
          </button>
        </div>

        {/* nav items */}
        <nav className="flex flex-1 flex-col gap-0.5 p-2 overflow-y-auto">
          {NAV_ITEMS.map(({ label, to, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/platform/tenants"}
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-lg px-2 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-gray-100 text-gray-900 font-medium"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                }`
              }
            >
              <Icon size={18} className="shrink-0 text-gray-400" />
              <span className="truncate">{label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* topbar */}
        <header className="flex h-12 shrink-0 items-center justify-between border-b border-gray-200 bg-white px-4">
          <button
            className="lg:hidden text-gray-400 hover:text-gray-700"
            onClick={() => setMobileOpen((o) => !o)}
          >
            <Menu size={20} />
          </button>
          <div className="flex items-center gap-4 ml-auto">
            {user && <span className="text-sm text-gray-500">{user.email}</span>}
            <button
              onClick={handleLogout}
              className="text-sm text-red-600 hover:underline"
            >
              Sair
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
