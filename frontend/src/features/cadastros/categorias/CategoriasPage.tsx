import { useState } from "react";
import { Button } from "@/components/ui/button";
import { CategoriaModal } from "./CategoriaModal";
import { useCategorias, useToggleCategoriaAtivo, type Categoria } from "./useCategorias";

type Filtro = "ativos" | "inativos" | "todos";

export function CategoriasPage() {
  const { data: categorias = [], isLoading } = useCategorias();
  const toggleAtivo = useToggleCategoriaAtivo();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Categoria | null>(null);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [filtro, setFiltro] = useState<Filtro>("ativos");

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

  const categoriasFiltradas = categorias.filter((cat) => {
    if (filtro === "ativos") return cat.ativo;
    if (filtro === "inativos") return !cat.ativo;
    return true;
  });

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Categorias</h1>
        <Button onClick={openCreate}>Nova Categoria</Button>
      </div>

      <div className="mb-3 flex gap-1">
        {(["ativos", "inativos", "todos"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFiltro(f)}
            className={`rounded border px-3 py-1 text-sm capitalize ${
              filtro === f ? "bg-gray-900 text-white" : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            {f === "ativos" ? "Ativos" : f === "inativos" ? "Inativos" : "Todos"}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : categoriasFiltradas.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhuma categoria encontrada.</p>
      ) : (
        <div className="rounded border divide-y text-sm">
          {categoriasFiltradas.map((cat) => {
            const childrenVisiveis = (cat.children ?? []).filter((ch) => {
              if (filtro === "ativos") return ch.ativo;
              if (filtro === "inativos") return !ch.ativo;
              return true;
            });
            const hasChildren = childrenVisiveis.length > 0;
            const isOpen = expanded.has(cat.id);

            return (
              <div key={cat.id}>
                <div className={`flex items-center justify-between px-4 py-2 hover:bg-gray-50 ${!cat.ativo ? "opacity-60" : "bg-white"}`}>
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
                    <span className={`font-medium ${cat.ativo ? "text-gray-900" : "text-gray-400 line-through"}`}>
                      {cat.nome}
                    </span>
                    {hasChildren && (
                      <span className="text-xs text-gray-400">
                        ({childrenVisiveis.length} subcategoria{childrenVisiveis.length !== 1 ? "s" : ""})
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
                      onClick={() => toggleAtivo.mutate(cat.id)}
                      disabled={toggleAtivo.isPending}
                      className={cat.ativo ? "text-yellow-600 hover:text-yellow-700" : "text-green-600 hover:text-green-700"}
                    >
                      {cat.ativo ? "Desativar" : "Reativar"}
                    </Button>
                  </div>
                </div>

                {hasChildren && isOpen && (
                  <div className="divide-y border-t bg-gray-50">
                    {childrenVisiveis.map((child) => (
                      <div
                        key={child.id}
                        className="flex items-center justify-between px-4 py-2 pl-10 hover:bg-gray-100"
                      >
                        <span className={child.ativo ? "text-gray-700" : "text-gray-400 line-through"}>
                          {child.nome}
                        </span>
                        <div className="flex gap-2">
                          <Button size="sm" variant="outline" onClick={() => openEdit(child)}>
                            Editar
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => toggleAtivo.mutate(child.id)}
                            disabled={toggleAtivo.isPending}
                            className={child.ativo ? "text-yellow-600 hover:text-yellow-700" : "text-green-600 hover:text-green-700"}
                          >
                            {child.ativo ? "Desativar" : "Reativar"}
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
    </div>
  );
}
