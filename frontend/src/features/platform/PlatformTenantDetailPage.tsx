import { useParams, Link } from "react-router-dom";
import { useTenantUsers } from "./usePlatformApi";

export function PlatformTenantDetailPage() {
  const { tenantId } = useParams<{ tenantId: string }>();
  const id = tenantId ? parseInt(tenantId, 10) : null;
  const { data: users = [], isLoading } = useTenantUsers(id);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Link to="/platform/tenants" className="text-sm text-blue-600 hover:underline">
          ← Tenants
        </Link>
        <h1 className="text-xl font-semibold text-gray-900">Usuários do Tenant #{tenantId}</h1>
      </div>

      {isLoading ? (
        <p className="text-sm text-gray-500">Carregando…</p>
      ) : (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 text-left">
              <tr>
                <th className="px-4 py-3 font-medium">Nome</th>
                <th className="px-4 py-3 font-medium">Username</th>
                <th className="px-4 py-3 font-medium">Perfil</th>
                <th className="px-4 py-3 font-medium">Último Login</th>
                <th className="px-4 py-3 font-medium">Ativo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{u.name}</td>
                  <td className="px-4 py-3 text-gray-500">{u.username}</td>
                  <td className="px-4 py-3">{u.profile_name}</td>
                  <td className="px-4 py-3 text-gray-500">
                    {u.last_login
                      ? new Date(u.last_login).toLocaleString("pt-BR")
                      : "Nunca"}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${u.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                      {u.is_active ? "Sim" : "Não"}
                    </span>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                    Nenhum usuário encontrado
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
