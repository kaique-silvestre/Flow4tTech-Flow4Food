import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { MetodoPagamentoModal } from "./MetodoPagamentoModal";
import { useDeleteMetodoPagamento, useMetodosPagamento, useToggleMetodoAtivo, type MetodoPagamento } from "./useMetodosPagamento";

export function MetodosPagamentoPage() {
  const { data: metodos = [], isLoading } = useMetodosPagamento();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<MetodoPagamento | null>(null);
  const [filtro, setFiltro] = useState<"ativos" | "inativos" | "todos">("ativos");
  const [removendo, setRemovendo] = useState<MetodoPagamento | null>(null);
  const deleteMutation = useDeleteMetodoPagamento();
  const toggle = useToggleMetodoAtivo();

  const metodosFiltrados = metodos.filter((m) =>
    filtro === "todos" ? true : filtro === "ativos" ? m.ativo : !m.ativo
  );

  function openCreate() {
    setEditing(null);
    setModalOpen(true);
  }

  function openEdit(m: MetodoPagamento) {
    setEditing(m);
    setModalOpen(true);
  }

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Métodos de Pagamento</h1>
        <Button onClick={openCreate}>Novo Método</Button>
      </div>

      <div className="mb-3 flex gap-1">
        {(["ativos", "inativos", "todos"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFiltro(f)}
            className={`rounded border px-3 py-1 text-sm capitalize ${filtro === f ? "bg-gray-900 text-white" : "bg-white text-gray-600 hover:bg-gray-50"}`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : metodosFiltrados.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum método de pagamento encontrado.</p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2 pr-4">Nome</th>
              <th className="py-2 pr-4">Status</th>
              <th className="py-2 pr-4" />
              <th className="py-2" />
            </tr>
          </thead>
          <tbody>
            {metodosFiltrados.map((m) => (
              <tr key={m.id} className="border-b last:border-0">
                <td className={`py-2 pr-4 ${!m.ativo ? "text-gray-400 line-through" : ""}`}>
                  {m.nome}
                </td>
                <td className="py-2 pr-4">
                  {m.ativo ? (
                    <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">
                      Ativo
                    </span>
                  ) : (
                    <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                      Inativo
                    </span>
                  )}
                </td>
                <td className="py-2 pr-4 text-right space-x-2">
                  <Button size="sm" variant="outline" onClick={() => openEdit(m)}>
                    Editar
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => toggle.mutate(m.id)}
                    className={m.ativo ? "text-yellow-600 hover:text-yellow-700" : "text-green-600 hover:text-green-700"}
                  >
                    {m.ativo ? "Desativar" : "Ativar"}
                  </Button>
                </td>
                <td className="py-2 text-right">
                  <Button size="sm" variant="destructive" onClick={() => setRemovendo(m)}>
                    Remover
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <MetodoPagamentoModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        editing={editing}
      />

      <ConfirmDialog
        open={!!removendo}
        title="Remover método de pagamento?"
        description={`Tem certeza que deseja remover "${removendo?.nome}"? Esta ação não pode ser desfeita.`}
        confirmLabel="Remover"
        onConfirm={() => {
          if (!removendo) return;
          deleteMutation.mutate(removendo.id, { onSuccess: () => setRemovendo(null), onError: () => setRemovendo(null) });
        }}
        onCancel={() => setRemovendo(null)}
        isPending={deleteMutation.isPending}
      />
    </div>
  );
}
