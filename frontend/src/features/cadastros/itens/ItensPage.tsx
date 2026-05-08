import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { useCategorias } from "@/features/cadastros/categorias/useCategorias";
import { formatCurrency } from "@/lib/format";
import { ItemModal } from "./ItemModal";
import { useDeleteItem, useItens, type ItemFilters, type ItemResponse } from "./useItens";

export function ItensPage() {
  const [filters, setFilters] = useState<ItemFilters>({});
  const { data: itens = [], isLoading } = useItens(filters);
  const { data: categorias = [] } = useCategorias();
  const deleteMutation = useDeleteItem();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<ItemResponse | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);

  function openCreate() {
    setEditing(null);
    setModalOpen(true);
  }

  function openEdit(item: ItemResponse) {
    setEditing(item);
    setModalOpen(true);
  }

  function handleDelete(id: number) {
    setConfirmDelete(id);
  }

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Itens</h1>
        <Button onClick={openCreate}>Novo Item</Button>
      </div>

      {/* Filtros */}
      <div className="mb-4 flex flex-wrap gap-4 text-sm">
        <div className="flex items-center gap-2">
          <span className="text-gray-500">Tipo:</span>
          {(["", "simples", "composto"] as const).map((t) => (
            <label key={t} className="flex cursor-pointer items-center gap-1">
              <input
                type="radio"
                name="tipo"
                value={t}
                checked={(filters.tipo ?? "") === t}
                onChange={() => setFilters((f) => ({ ...f, tipo: t || null }))}
              />
              {t === "" ? "Todos" : t.charAt(0).toUpperCase() + t.slice(1)}
            </label>
          ))}
        </div>

        <select
          className="rounded border px-2 py-1 text-sm"
          value={filters.categoria_id ?? ""}
          onChange={(e) =>
            setFilters((f) => ({ ...f, categoria_id: e.target.value ? Number(e.target.value) : null }))
          }
        >
          <option value="">Todas as categorias</option>
          {categorias.map((c) => (
            <option key={c.id} value={c.id}>{c.nome}</option>
          ))}
        </select>

        <select
          className="rounded border px-2 py-1 text-sm"
          value={filters.vendavel == null ? "" : String(filters.vendavel)}
          onChange={(e) =>
            setFilters((f) => ({
              ...f,
              vendavel: e.target.value === "" ? null : e.target.value === "true",
            }))
          }
        >
          <option value="">Vendável: Todos</option>
          <option value="true">Sim</option>
          <option value="false">Não</option>
        </select>

        <input
          className="rounded border px-2 py-1 text-sm"
          placeholder="Buscar nome..."
          value={filters.busca ?? ""}
          onChange={(e) => setFilters((f) => ({ ...f, busca: e.target.value || null }))}
        />
      </div>

      {/* Tabela */}
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : itens.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum item encontrado.</p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2 pr-4">Nome</th>
              <th className="py-2 pr-4">Tipo</th>
              <th className="py-2 pr-4">Vendável</th>
              <th className="py-2 pr-4">Preço</th>
              <th className="py-2" />
            </tr>
          </thead>
          <tbody>
            {itens.map((item) => (
              <tr key={item.id} className="border-b last:border-0">
                <td className="py-2 pr-4 font-medium">{item.nome}</td>
                <td className="py-2 pr-4 capitalize text-gray-600">{item.tipo}</td>
                <td className="py-2 pr-4">
                  {item.vendavel ? (
                    <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">Sim</span>
                  ) : (
                    <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">Não</span>
                  )}
                </td>
                <td className="py-2 pr-4 text-gray-600">
                  {item.preco_venda != null ? formatCurrency(item.preco_venda) : "—"}
                </td>
                <td className="py-2 text-right">
                  <Button size="sm" variant="outline" onClick={() => openEdit(item)} className="mr-2">
                    Editar
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDelete(item.id)}
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

      <ItemModal open={modalOpen} onClose={() => setModalOpen(false)} editing={editing} />
      <ConfirmDialog
        open={confirmDelete !== null}
        title="Remover item?"
        description="Se referenciado em ficha técnica, será apenas inativado."
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
