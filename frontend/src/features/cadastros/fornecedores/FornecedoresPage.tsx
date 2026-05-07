import { useState } from "react";
import { Button } from "@/components/ui/button";
import { FornecedorModal } from "./FornecedorModal";
import { useFornecedores, useDeleteFornecedor, type Fornecedor } from "./useFornecedores";

export function FornecedoresPage() {
  const { data: fornecedores = [], isLoading } = useFornecedores();
  const deleteMutation = useDeleteFornecedor();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Fornecedor | null>(null);

  function openCreate() {
    setEditing(null);
    setModalOpen(true);
  }

  function openEdit(f: Fornecedor) {
    setEditing(f);
    setModalOpen(true);
  }

  function handleDelete(id: number) {
    if (confirm("Remover fornecedor?")) {
      deleteMutation.mutate(id);
    }
  }

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Fornecedores</h1>
        <Button onClick={openCreate}>Novo Fornecedor</Button>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : fornecedores.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum fornecedor cadastrado.</p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2 pr-4">Nome</th>
              <th className="py-2 pr-4">Telefone</th>
              <th className="py-2 pr-4">E-mail</th>
              <th className="py-2" />
            </tr>
          </thead>
          <tbody>
            {fornecedores.map((f) => (
              <tr key={f.id} className="border-b last:border-0">
                <td className="py-2 pr-4">{f.nome}</td>
                <td className="py-2 pr-4 text-gray-600">{f.telefone ?? "—"}</td>
                <td className="py-2 pr-4 text-gray-600">{f.email ?? "—"}</td>
                <td className="py-2 text-right">
                  <Button size="sm" variant="outline" onClick={() => openEdit(f)} className="mr-2">
                    Editar
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDelete(f.id)}
                    className="text-red-600 hover:text-red-700"
                  >
                    Remover
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <FornecedorModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        editing={editing}
      />
    </div>
  );
}
