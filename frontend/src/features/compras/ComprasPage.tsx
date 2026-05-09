import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Input } from "@/components/ui/input";
import { useFornecedores } from "@/features/cadastros/fornecedores/useFornecedores";
import { formatCurrency } from "@/lib/format";
import { useCancelarCompra, useCompras, usePatchCompra, type CompraFilters, type CompraResponse } from "./useCompras";

export function ComprasPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<CompraFilters>({});
  const { data: compras = [], isLoading } = useCompras(filters);
  const { data: fornecedores = [] } = useFornecedores();
  const cancelarMutation = useCancelarCompra();
  const patchMutation = usePatchCompra();

  const [cancelando, setCancelando] = useState<CompraResponse | null>(null);
  const [editando, setEditando] = useState<CompraResponse | null>(null);
  const [editFornecedorId, setEditFornecedorId] = useState<string>("");
  const [editDataCompra, setEditDataCompra] = useState<string>("");
  const [editNumeroNota, setEditNumeroNota] = useState<string>("");

  const total = compras.reduce((sum, c) => sum + Number(c.total), 0);

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Compras</h1>
        <Button onClick={() => navigate("/compras/nova")}>+ Nova Compra</Button>
      </div>

      {/* Filtros */}
      <div className="mb-4 flex flex-wrap gap-3 text-sm">
        <div className="flex items-center gap-2">
          <label className="text-gray-500">De:</label>
          <input
            type="date"
            className="rounded border px-2 py-1 text-sm"
            value={filters.data_inicio ?? ""}
            onChange={(e) => setFilters((f) => ({ ...f, data_inicio: e.target.value || null }))}
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-gray-500">Até:</label>
          <input
            type="date"
            className="rounded border px-2 py-1 text-sm"
            value={filters.data_fim ?? ""}
            onChange={(e) => setFilters((f) => ({ ...f, data_fim: e.target.value || null }))}
          />
        </div>
        <select
          className="rounded border px-2 py-1 text-sm"
          value={filters.fornecedor_id ?? ""}
          onChange={(e) =>
            setFilters((f) => ({ ...f, fornecedor_id: e.target.value ? Number(e.target.value) : null }))
          }
        >
          <option value="">Todos os fornecedores</option>
          {fornecedores.map((f) => (
            <option key={f.id} value={f.id}>{f.nome}</option>
          ))}
        </select>
      </div>

      {/* Lista */}
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => <div key={i} className="h-14 animate-pulse rounded bg-gray-100" />)}
        </div>
      ) : compras.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhuma compra encontrada.</p>
      ) : (
        <div className="space-y-2">
          {compras.map((compra) => (
            <div key={compra.id} className={`flex items-center justify-between rounded border p-3 ${compra.status === "cancelada" ? "text-gray-400" : ""}`}>
              <div>
                <div className="font-medium flex items-center gap-2">
                  <span className="text-gray-400 font-normal">#{String(compra.id).padStart(4, "0")}</span>
                  {new Date(compra.data_compra + "T00:00:00").toLocaleDateString("pt-BR")}
                  {" · "}
                  <span className={compra.status === "cancelada" ? "text-gray-400" : "text-gray-600"}>{compra.fornecedor_nome ?? "Sem fornecedor"}</span>
                  {compra.status === "cancelada" && (
                    <span className="rounded-full bg-gray-200 px-2 py-0.5 text-xs text-gray-500">Cancelada</span>
                  )}
                </div>
                <div className="text-xs text-gray-400">
                  Nota: {compra.numero_nota ?? "—"} · {compra.itens.length} {compra.itens.length === 1 ? "item" : "itens"}
                </div>
              </div>
              <div className="flex items-center gap-2 text-right">
                <div className={`font-semibold ${compra.status === "cancelada" ? "line-through" : ""}`}>{formatCurrency(compra.total)}</div>
                {compra.status === "ativa" && (
                  <>
                    <Button size="sm" variant="outline" onClick={() => {
                      setEditando(compra);
                      setEditFornecedorId(compra.fornecedor_id ? String(compra.fornecedor_id) : "");
                      setEditDataCompra(compra.data_compra);
                      setEditNumeroNota(compra.numero_nota ?? "");
                    }}>
                      Editar
                    </Button>
                    <Button size="sm" variant="destructive" onClick={() => setCancelando(compra)}>
                      Cancelar Nota
                    </Button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {compras.length > 0 && (
        <div className="mt-4 text-right text-sm text-gray-500">
          Total no período: <span className="font-semibold text-gray-800">{formatCurrency(total)}</span>
        </div>
      )}

      <ConfirmDialog
        open={!!cancelando}
        title="Cancelar nota fiscal?"
        description={`A nota #${String(cancelando?.id ?? 0).padStart(4, "0")} será cancelada e o estoque será revertido.`}
        confirmLabel="Cancelar Nota"
        onConfirm={() => {
          if (cancelando) cancelarMutation.mutate(cancelando.id, { onSuccess: () => setCancelando(null) });
        }}
        onCancel={() => setCancelando(null)}
      />

      {editando && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
            <h2 className="mb-4 text-lg font-semibold">Editar Compra #{String(editando.id).padStart(4, "0")}</h2>
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-sm text-gray-600">Fornecedor</label>
                <select
                  className="w-full rounded border px-2 py-1.5 text-sm"
                  value={editFornecedorId}
                  onChange={(e) => setEditFornecedorId(e.target.value)}
                >
                  <option value="">Sem fornecedor</option>
                  {fornecedores.map((f) => (
                    <option key={f.id} value={f.id}>{f.nome}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm text-gray-600">Data da Compra</label>
                <Input
                  type="date"
                  value={editDataCompra}
                  onChange={(e) => setEditDataCompra(e.target.value)}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-gray-600">Número da Nota</label>
                <Input
                  value={editNumeroNota}
                  onChange={(e) => setEditNumeroNota(e.target.value)}
                  placeholder="Opcional"
                />
              </div>
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setEditando(null)}>Cancelar</Button>
              <Button
                onClick={() => {
                  patchMutation.mutate(
                    {
                      id: editando.id,
                      data: {
                        fornecedor_id: editFornecedorId ? Number(editFornecedorId) : null,
                        data_compra: editDataCompra,
                        numero_nota: editNumeroNota || null,
                      },
                    },
                    { onSuccess: () => setEditando(null) },
                  );
                }}
              >
                Salvar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
