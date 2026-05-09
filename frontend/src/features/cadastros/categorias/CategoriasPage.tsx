import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { CategoriaModal } from "./CategoriaModal";
import { useCategorias, useDeleteCategoria, type Categoria } from "./useCategorias";

export function CategoriasPage() {
  const { data: categorias = [], isLoading } = useCategorias();
  const deleteMutation = useDeleteCategoria();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Categoria | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  function openCreate() {
    setEditing(null);
    setModalOpen(true);
  }

  function openEdit(cat: Categoria) {
    setEditing(cat);
    setModalOpen(true);
  }

  function toggleExpand(id: number) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
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
        <div className="rounded border divide-y text-sm">
          {categorias.map((cat) => {
            const hasChildren = (cat.children ?? []).length > 0;
            const isOpen = expanded.has(cat.id);

            return (
              <div key={cat.id}>
                {/* Parent row */}
                <div className="flex items-center justify-between px-4 py-2 bg-white hover:bg-gray-50">
                  <div className="flex items-center gap-2">
                    {hasChildren ? (
                      <button
                        onClick={() => toggleExpand(cat.id)}
                        className="text-gray-400 hover:text-gray-700 w-4 text-xs"
                      >
                        {isOpen ? "▼" : "▶"}
                      </button>
                    ) : (
                      <span className="w-4" />
                    )}
                    <span className="font-medium text-gray-900">{cat.nome}</span>
                    {hasChildren && (
                      <span className="text-xs text-gray-400">
                        ({cat.children.length} subcategoria{cat.children.length !== 1 ? "s" : ""})
                      </span>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => openEdit(cat)}>
                      Editar
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setConfirmDelete(cat.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      Remover
                    </Button>
                  </div>
                </div>

                {/* Children rows */}
                {hasChildren && isOpen && (
                  <div className="divide-y border-t bg-gray-50">
                    {cat.children.map((child) => (
                      <div
                        key={child.id}
                        className="flex items-center justify-between px-4 py-2 pl-10 hover:bg-gray-100"
                      >
                        <span className="text-gray-700">{child.nome}</span>
                        <div className="flex gap-2">
                          <Button size="sm" variant="outline" onClick={() => openEdit(child)}>
                            Editar
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setConfirmDelete(child.id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            Remover
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      <CategoriaModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        editing={editing}
      />
      <ConfirmDialog
        open={confirmDelete !== null}
        title="Remover categoria?"
        confirmLabel="Remover"
        onConfirm={() => {
          deleteMutation.mutate(confirmDelete!);
          setConfirmDelete(null);
        }}
        onCancel={() => setConfirmDelete(null)}
        isPending={deleteMutation.isPending}
      />
    </div>
  );
}
