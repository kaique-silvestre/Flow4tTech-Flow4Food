import { Link, Outlet, useNavigate } from "react-router-dom";
import { usePlatformAuthStore } from "@/stores/platformAuthStore";

export function PlatformLayout() {
  const { user, clearToken } = usePlatformAuthStore();
  const navigate = useNavigate();

  function handleLogout() {
    clearToken();
    void navigate("/platform/login");
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-3 flex items-center justify-between">
        <Link to="/platform/tenants" className="text-lg font-bold text-gray-900">
          Flow4Tech Admin
        </Link>
        <div className="flex items-center gap-4">
          {user && <span className="text-sm text-gray-500">{user.email}</span>}
          <button
            onClick={handleLogout}
            className="text-sm text-red-600 hover:underline"
          >
            Sair
          </button>
        </div>
      </header>
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  );
}
