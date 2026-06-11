import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "@/lib/toast";
import { useTenants, useUpdateAssinatura, type TenantListItem } from "./usePlatformApi";

const STATUS_OPTIONS = ["", "trial", "ativa", "suspensa", "cancelada"] as const;

const STATUS_LABELS: Record<string, string> = {
  trial: "Trial",
  ativa: "Ativa",
  suspensa: "Suspensa",
  cancelada: "Cancelada",
};

const STATUS_COLORS: Record<string, string> = {
  trial: "bg-yellow-100 text-yellow-800",
  ativa: "bg-green-100 text-green-800",
  suspensa: "bg-red-100 text-red-800",
  cancelada: "bg-gray-100 text-gray-600",
};

export function PlatformTenantsPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const { data: tenants = [], isLoading } = useTenants(statusFilter || undefined);
  const updateAssinatura = useUpdateAssinatura();
  const navigate = useNavigate();

  function handleStatusChange(tenant: TenantListItem, newStatus: string) {
    updateAssinatura.mutate(
      { tenantId: tenant.id, status: newStatus },
      {
        onSuccess: () => toast.success(`Assinatura de ${tenant.nome_fantasia} atualizada`),
        onError: () => toast.error("Erro ao atualizar assinatura"),
      }
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Tenants</h1>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todos os status</option>
          {STATUS_OPTIONS.filter(Boolean).map((s) => (
            <option key={s} value={s}>{STATUS_LABELS[s]}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <p className="text-sm text-gray-500">Carregando…</p>
      ) : (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 text-left">
              <tr>
                <th className="px-4 py-3 font-medium">Empresa</th>
                <th className="px-4 py-3 font-medium">CNPJ</th>
                <th className="px-4 py-3 font-medium">Status Tenant</th>
                <th className="px-4 py-3 font-medium">Assinatura</th>
                <th className="px-4 py-3 font-medium">Vencimento</th>
                <th className="px-4 py-3 font-medium">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {tenants.map((t) => (
                <tr
                  key={t.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => void navigate(`/platform/tenants/${t.id}`)}
                >
                  <td className="px-4 py-3 font-medium text-gray-900">{t.nome_fantasia}</td>
                  <td className="px-4 py-3 text-gray-500">{t.cnpj ?? "—"}</td>
                  <td className="px-4 py-3">
                    <span className="capitalize">{t.status_tenant}</span>
                  </td>
                  <td className="px-4 py-3">
                    {t.status_assinatura ? (
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[t.status_assinatura] ?? ""}`}>
                        {STATUS_LABELS[t.status_assinatura] ?? t.status_assinatura}
                      </span>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {t.data_vencimento
                      ? new Date(t.data_vencimento).toLocaleDateString("pt-BR")
                      : "—"}
                  </td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <div className="flex gap-2">
                      {t.status_assinatura !== "ativa" && (
                        <button
                          onClick={() => handleStatusChange(t, "ativa")}
                          className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200"
                        >
                          Ativar
                        </button>
                      )}
                      {t.status_assinatura !== "suspensa" && (
                        <button
                          onClick={() => handleStatusChange(t, "suspensa")}
                          className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200"
                        >
                          Suspender
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {tenants.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                    Nenhum tenant encontrado
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
