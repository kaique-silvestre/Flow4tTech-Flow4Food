import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Pagination, paginar } from "@/components/ui/pagination";
import { InsumoEditModal } from "./InsumoEditModal";
import {
  useAllInsumos,
  useToggleInsumoAtivo,
  useDeleteInsumo,
  type InsumoResponse,
} from "@/features/estoque/useInsumos";

type Filtro = "ativos" | "inativos" | "todos";

const POR_PAGINA = 12;

export function InsumosPage() {
  const { data: insumos = [], isLoading } = useAllInsumos();
  const toggleAtivo = useToggleInsumoAtivo();
  const deleteMutation = useDeleteInsumo();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<InsumoResponse | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);
  const [filtro, setFiltro] = useState<Filtro>("ativos");
  const [pagina, setPagina] = useState(1);

  const insumosFiltrados = insumos.filter((i) =>
    filtro === "todos" ? true : filtro === "ativos" ? i.ativo : !i.ativo,
  );

  function openCreate() {
    setEditing(null);
    setModalOpen(true);
  }

  function openEdit(i: InsumoResponse) {
    setEditing(i);
    setModalOpen(true);
  }

  return (
    <div className="p-6 min-h-full flex flex-col">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Insumos</h1>
        <Button onClick={openCreate}>Novo Insumo</Button>
      </div>

      <div className="mb-3 flex gap-1">
        {(["ativos", "inativos", "todos"] as const).map((f) => (
          <button
            key={f}
            onClick={() => { setFiltro(f); setPagina(1); }}
            className={`rounded border px-3 py-1 text-sm capitalize ${
              filtro === f ? "bg-gray-900 text-white" : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
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
      ) : insumosFiltrados.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum insumo encontrado.</p>
      ) : (
        <div className="flex-1 flex flex-col">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2 pr-4">Nome</th>
              <th className="py-2 pr-4">Estoque</th>
              <th className="py-2 pr-4">Unidade</th>
              <th className="py-2 pr-4">Status</th>
              <th className="py-2" />
            </tr>
          </thead>
          <tbody>
            {paginar(insumosFiltrados, pagina, POR_PAGINA).map((insumo) => (
              <tr key={insumo.id} className="border-b last:border-0">
                <td className={`py-2 pr-4 ${!insumo.ativo ? "text-gray-400 line-through" : ""}`}>
                  {insumo.nome}
                </td>
                <td className="py-2 pr-4 text-gray-600">
                  {insumo.unidade_base === "kg"
                    ? Number(insumo.estoque_atual).toFixed(3)
                    : Math.round(Number(insumo.estoque_atual)).toString()}
                </td>
                <td className="py-2 pr-4 text-gray-600">{insumo.unidade_base}</td>
                <td className="py-2 pr-4">
                  {insumo.ativo ? (
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
                  <div className="flex justify-end gap-2">
                    <Button size="sm" variant="outline" onClick={() => openEdit(insumo)}>
                      Editar
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => toggleAtivo.mutate(insumo.id)}
                      disabled={toggleAtivo.isPending}
                    >
                      {insumo.ativo ? "Desativar" : "Reativar"}
                    </Button>
                    {!insumo.ativo && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setConfirmDelete(insumo.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        Remover
                      </Button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="flex-1" />
        <Pagination
          pagina={pagina}
          totalPaginas={Math.ceil(insumosFiltrados.length / POR_PAGINA)}
          total={insumosFiltrados.length}
          label="insumos"
          onPageChange={setPagina}
        />
        </div>
      )}

      <InsumoEditModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        editing={editing}
      />
      <ConfirmDialog
        open={confirmDelete !== null}
        title="Remover insumo?"
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
