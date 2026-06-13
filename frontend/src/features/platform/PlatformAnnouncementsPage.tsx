import { useState } from "react";
import { toast } from "@/lib/toast";
import { usePlatformAnnouncements, useCreateAnnouncement, useTenants } from "./usePlatformApi";
import type { AnnouncementCreate } from "./usePlatformApi";

const TARGET_LABELS: Record<string, string> = {
  all: "Todos os tenants",
  specific: "Tenants específicos",
};

function AnnouncementModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [target, setTarget] = useState<"all" | "specific">("all");
  const [selectedTenants, setSelectedTenants] = useState<number[]>([]);
  const { data: tenants = [] } = useTenants();
  const create = useCreateAnnouncement();

  if (!open) return null;

  function toggleTenant(id: number) {
    setSelectedTenants((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]
    );
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !body.trim()) {
      toast.error("Título e mensagem são obrigatórios");
      return;
    }
    if (target === "specific" && selectedTenants.length === 0) {
      toast.error("Selecione ao menos um tenant");
      return;
    }
    const payload: AnnouncementCreate = {
      title: title.trim(),
      body: body.trim(),
      expires_at: expiresAt || null,
      target,
      tenant_ids: target === "specific" ? selectedTenants : [],
    };
    create.mutate(payload, {
      onSuccess: () => {
        toast.success("Comunicado criado");
        onClose();
        setTitle("");
        setBody("");
        setExpiresAt("");
        setTarget("all");
        setSelectedTenants([]);
      },
      onError: () => toast.error("Erro ao criar comunicado"),
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Novo Comunicado</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Título</label>
            <input
              className="mt-1 w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ex: Manutenção programada"
              maxLength={200}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Mensagem</label>
            <textarea
              className="mt-1 w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={4}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Texto do comunicado..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Data de expiração</label>
            <input
              type="datetime-local"
              className="mt-1 w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={expiresAt}
              onChange={(e) => setExpiresAt(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Destinatários</label>
            <select
              className="mt-1 w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={target}
              onChange={(e) => setTarget(e.target.value as "all" | "specific")}
            >
              <option value="all">Todos os tenants</option>
              <option value="specific">Tenants específicos</option>
            </select>
          </div>
          {target === "specific" && (
            <div className="max-h-40 overflow-y-auto rounded-lg border p-2 space-y-1">
              {tenants.map((t) => (
                <label key={t.id} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedTenants.includes(t.id)}
                    onChange={() => toggleTenant(t.id)}
                  />
                  {t.nome_fantasia}
                </label>
              ))}
            </div>
          )}
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

export function PlatformAnnouncementsPage() {
  const { data: announcements = [], isLoading } = usePlatformAnnouncements();
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Comunicados</h1>
        <button
          onClick={() => setModalOpen(true)}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
        >
          + Novo comunicado
        </button>
      </div>

      {isLoading ? (
        <p className="text-sm text-gray-500">Carregando...</p>
      ) : announcements.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum comunicado criado.</p>
      ) : (
        <div className="rounded-xl border bg-white overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b">
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Título</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Destinatários</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Expira em</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Leituras</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {announcements.map((ann) => (
                <tr key={ann.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{ann.title}</td>
                  <td className="px-4 py-3 text-gray-600">{TARGET_LABELS[ann.target] ?? ann.target}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {ann.expires_at
                      ? new Date(ann.expires_at).toLocaleString("pt-BR")
                      : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        ann.is_active
                          ? "bg-green-100 text-green-800"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {ann.is_active ? "Ativo" : "Inativo"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-gray-900 font-medium">{ann.read_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <AnnouncementModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}
