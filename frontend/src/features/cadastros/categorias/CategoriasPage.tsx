import { useState } from "react";
import { Button } from "@/components/ui/button";
import { CategoriaModal } from "./CategoriaModal";
import { useCategorias, useDeleteCategoria, type Categoria } from "./useCategorias";

export function CategoriasPage() {
  const { data: categorias = [], isLoading } = useCategorias();
  const deleteMutation = useDeleteCategoria();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Categoria | null>(null);

  function openCreate() {
    setEditing(null);
    setModalOpen(true);
  }

  function openEdit(cat: Categoria) {
    setEditing(cat);
    setModalOpen(true);
  }

  function handleDelete(id: number) {
    if (confirm("Remover categoria?")) {
      deleteMutation.mutate(id);
    }
  }

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Categorias</h1>
        <Button onClick={openCreate}>Nova Categoria</Button>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : categorias.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhuma categoria cadastrada.</p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2 pr-4">Nome</th>
              <th className="py-2" />
            </tr>
          </thead>
          <tbody>
            {categorias.map((cat) => (
              <tr key={cat.id} className="border-b last:border-0">
                <td className="py-2 pr-4">{cat.nome}</td>
                <td className="py-2 text-right">
                  <Button size="sm" variant="outline" onClick={() => openEdit(cat)} className="mr-2">
                    Editar
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDelete(cat.id)}
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

      <CategoriaModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        editing={editing}
      />
    </div>
  );
}
