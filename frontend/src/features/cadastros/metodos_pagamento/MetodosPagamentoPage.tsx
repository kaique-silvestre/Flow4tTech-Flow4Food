import { useState } from "react";
import { Button } from "@/components/ui/button";
import { MetodoPagamentoModal } from "./MetodoPagamentoModal";
import { useMetodosPagamento, type MetodoPagamento } from "./useMetodosPagamento";

export function MetodosPagamentoPage() {
  const { data: metodos = [], isLoading } = useMetodosPagamento();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<MetodoPagamento | null>(null);

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

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : metodos.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum método de pagamento cadastrado.</p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2 pr-4">Nome</th>
              <th className="py-2 pr-4">Status</th>
              <th className="py-2" />
            </tr>
          </thead>
          <tbody>
            {metodos.map((m) => (
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
                <td className="py-2 text-right">
                  <Button size="sm" variant="outline" onClick={() => openEdit(m)}>
                    Editar
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
    </div>
  );
}
