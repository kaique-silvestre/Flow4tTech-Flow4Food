import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "@/lib/toast";
import { useTenants, useUpdateAssinatura, useCreateTenant, type TenantListItem } from "./usePlatformApi";

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

function CreateTenantModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [nomeFantasia, setNomeFantasia] = useState("");
  const [cnpj, setCnpj] = useState("");
  const [maxUsers, setMaxUsers] = useState(10);
  const [trialDays, setTrialDays] = useState(14);
  const [adminName, setAdminName] = useState("");
  const [adminUsername, setAdminUsername] = useState("");
  const [adminEmail, setAdminEmail] = useState("");
  const [adminPassword, setAdminPassword] = useState("");
  const create = useCreateTenant();

  if (!open) return null;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!nomeFantasia.trim() || !adminName.trim() || !adminUsername.trim() || !adminEmail.trim() || !adminPassword) {
      toast.error("Preencha os dados da empresa e do administrador");
      return;
    }
    create.mutate(
      {
        nome_fantasia: nomeFantasia.trim(),
        cnpj: cnpj.trim() || undefined,
        max_users: maxUsers,
        trial_days: trialDays,
        admin_name: adminName.trim(),
        admin_username: adminUsername.trim(),
        admin_email: adminEmail.trim(),
        admin_password: adminPassword,
      },
      {
        onSuccess: () => {
          toast.success("Empresa criada com sucesso");
          onClose();
          setNomeFantasia("");
          setCnpj("");
          setMaxUsers(10);
          setTrialDays(14);
          setAdminName("");
          setAdminUsername("");
          setAdminEmail("");
          setAdminPassword("");
        },
        onError: () => toast.error("Erro ao criar empresa"),
      }
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Nova Empresa</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Nome Fantasia *</label>
            <input
              className="mt-1 w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={nomeFantasia}
              onChange={(e) => setNomeFantasia(e.target.value)}
              placeholder="Nome da empresa"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">CNPJ</label>
            <input
              className="mt-1 w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={cnpj}
              onChange={(e) => setCnpj(e.target.value)}
              placeholder="00.000.000/0001-00"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Máx. usuários</label>
              <input
                type="number"
                min={1}
                className="mt-1 w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={maxUsers}
                onChange={(e) => setMaxUsers(parseInt(e.target.value, 10) || 10)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Trial (dias)</label>
              <input
                type="number"
                min={1}
                className="mt-1 w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={trialDays}
                onChange={(e) => setTrialDays(parseInt(e.target.value, 10) || 14)}
              />
            </div>
          </div>
          <fieldset className="space-y-4 border-t pt-4">
            <legend className="text-sm font-medium text-gray-700">Administrador inicial</legend>
            <div>
              <label className="block text-sm font-medium text-gray-700">Nome *</label>
              <input className="mt-1 w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" value={adminName} onChange={(e) => setAdminName(e.target.value)} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Usuário *</label>
              <input className="mt-1 w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" value={adminUsername} onChange={(e) => setAdminUsername(e.target.value)} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">E-mail *</label>
              <input type="email" className="mt-1 w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" value={adminEmail} onChange={(e) => setAdminEmail(e.target.value)} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Senha *</label>
              <input type="password" minLength={6} className="mt-1 w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" value={adminPassword} onChange={(e) => setAdminPassword(e.target.value)} />
            </div>
          </fieldset>
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg px-4 py-2 text-sm text-gray-700 border hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={create.isPending}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {create.isPending ? "Criando..." : "Criar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function PlatformTenantsPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const { data, isLoading } = useTenants(statusFilter || undefined, page);
  const tenants = data?.items ?? [];
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
        <h1 className="text-xl font-semibold text-gray-900">Empresas</h1>
        <div className="flex items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="border rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todos os status</option>
            {STATUS_OPTIONS.filter(Boolean).map((s) => (
              <option key={s} value={s}>{STATUS_LABELS[s]}</option>
            ))}
          </select>
          <button
            onClick={() => setModalOpen(true)}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
          >
            + Nova Empresa
          </button>
        </div>
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
                <th className="px-4 py-3 font-medium">Usuários</th>
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
                  <td className="px-4 py-3 text-gray-500">
                    {t.qtd_usuarios ?? 0}/{t.max_users}
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
                    Nenhuma empresa encontrada
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-end gap-3 text-sm text-gray-600">
          <span>Página {data.page} de {data.total_pages} ({data.total} empresas)</span>
          <button
            type="button"
            onClick={() => setPage((current) => current - 1)}
            disabled={page === 1}
            className="rounded border px-3 py-1 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Anterior
          </button>
          <button
            type="button"
            onClick={() => setPage((current) => current + 1)}
            disabled={page >= data.total_pages}
            className="rounded border px-3 py-1 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Próxima
          </button>
        </div>
      )}

      <CreateTenantModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}
