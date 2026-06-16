import { useState } from "react";
import { Shield } from "lucide-react";
import { useAuditLogs } from "./usePlatformApi";
import type { AuditLogFilters } from "./usePlatformApi";

const PAGE_SIZE = 20;

function formatDate(iso: string) {
  return new Date(iso).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function PlatformAuditPage() {
  const [filters, setFilters] = useState<AuditLogFilters>({ page: 1, page_size: PAGE_SIZE });
  const [tenantIdInput, setTenantIdInput] = useState("");
  const [userIdInput, setUserIdInput] = useState("");
  const [actionInput, setActionInput] = useState("");
  const [dateFromInput, setDateFromInput] = useState("");
  const [dateToInput, setDateToInput] = useState("");

  const { data, isLoading } = useAuditLogs(filters);

  function applyFilters() {
    setFilters({
      page: 1,
      page_size: PAGE_SIZE,
      tenant_id: tenantIdInput ? Number(tenantIdInput) : undefined,
      user_id: userIdInput ? Number(userIdInput) : undefined,
      action: actionInput || undefined,
      date_from: dateFromInput || undefined,
      date_to: dateToInput || undefined,
    });
  }

  function clearFilters() {
    setTenantIdInput("");
    setUserIdInput("");
    setActionInput("");
    setDateFromInput("");
    setDateToInput("");
    setFilters({ page: 1, page_size: PAGE_SIZE });
  }

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 1;
  const currentPage = filters.page ?? 1;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
        <Shield size={20} className="text-indigo-600" />
        Log de Auditoria
      </h1>

      {/* Filters */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 mb-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Tenant ID</label>
            <input
              type="number"
              className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
              placeholder="ID do tenant"
              value={tenantIdInput}
              onChange={(e) => setTenantIdInput(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Usuário ID</label>
            <input
              type="number"
              className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
              placeholder="ID do usuário"
              value={userIdInput}
              onChange={(e) => setUserIdInput(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Ação</label>
            <input
              type="text"
              className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
              placeholder="ex: user.create"
              value={actionInput}
              onChange={(e) => setActionInput(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">De</label>
            <input
              type="datetime-local"
              className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
              value={dateFromInput}
              onChange={(e) => setDateFromInput(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Até</label>
            <input
              type="datetime-local"
              className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
              value={dateToInput}
              onChange={(e) => setDateToInput(e.target.value)}
            />
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={applyFilters}
            className="px-3 py-1.5 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700"
          >
            Filtrar
          </button>
          <button
            onClick={clearFilters}
            className="px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200"
          >
            Limpar
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-400 text-sm">Carregando...</div>
        ) : !data || data.items.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">Nenhum registro encontrado.</div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Timestamp</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Tenant</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Usuário</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Ação</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Entidade</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Impersonation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.items.map((log) => (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-gray-700 whitespace-nowrap">
                        {formatDate(log.created_at)}
                      </td>
                      <td className="px-4 py-3 text-gray-700">
                        {log.tenant_name ?? (log.tenant_id ? `#${log.tenant_id}` : "—")}
                      </td>
                      <td className="px-4 py-3 text-gray-700">
                        {log.user_name ?? (log.user_id ? `#${log.user_id}` : "—")}
                      </td>
                      <td className="px-4 py-3">
                        <span className="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded text-gray-800">
                          {log.action}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-600 text-xs">
                        {log.entity ? (
                          <>
                            {log.entity}
                            {log.entity_id != null && <span className="ml-1 text-gray-400">#{log.entity_id}</span>}
                          </>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {log.impersonated_by != null ? (
                          <span className="inline-flex items-center gap-1 text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full font-medium">
                            <Shield size={10} />
                            Admin #{log.impersonated_by}
                          </span>
                        ) : (
                          <span className="text-gray-300">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
                <span className="text-xs text-gray-500">
                  {data.total} registros · página {currentPage} de {totalPages}
                </span>
                <div className="flex gap-2">
                  <button
                    disabled={currentPage <= 1}
                    onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) - 1 }))}
                    className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-40 hover:bg-gray-50"
                  >
                    Anterior
                  </button>
                  <button
                    disabled={currentPage >= totalPages}
                    onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) + 1 }))}
                    className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-40 hover:bg-gray-50"
                  >
                    Próxima
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
