import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useFornecedores } from "@/features/cadastros/fornecedores/useFornecedores";
import { formatCurrency } from "@/lib/format";
import { useCancelarCompra, useCompras, usePatchCompra, type CompraFilters, type CompraResponse } from "./useCompras";
import { ChevronRight, ChevronDown } from "lucide-react";

const STATUS_OPTS = [
  { value: "ativa", label: "Ativas" },
  { value: "", label: "Todas" },
  { value: "cancelada", label: "Canceladas" },
] as const;

export function ComprasPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<CompraFilters>({ status: "ativa" });
  const [pagina, setPagina] = useState(1);
  const { data: paginado, isLoading } = useCompras({ ...filters, pagina, por_pagina: 8 });
  const compras = paginado?.itens ?? [];
  const totalPaginas = paginado?.total_paginas ?? 1;

  function atualizarFiltro(update: Partial<CompraFilters>) {
    setFilters((f) => ({ ...f, ...update }));
    setPagina(1);
  }
  const { data: fornecedores = [] } = useFornecedores();
  const cancelarMutation = useCancelarCompra();
  const patchMutation = usePatchCompra();

  const [expandidos, setExpandidos] = useState<Set<number>>(new Set());
  const [cancelando, setCancelando] = useState<CompraResponse | null>(null);
  const [editando, setEditando] = useState<CompraResponse | null>(null);

  function toggleExpandir(id: number) {
    setExpandidos((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }
  const [editFornecedorId, setEditFornecedorId] = useState<string>("");
  const [editDataCompra, setEditDataCompra] = useState<string>("");
  const [editNumeroNota, setEditNumeroNota] = useState<string>("");

  const totalPeriodo = paginado?.total_periodo ?? 0;

  return (
    <div className="p-6 min-h-full flex flex-col">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Compras</h1>
        <Button onClick={() => navigate("/compras/nova")}>+ Nova Compra</Button>
      </div>

      {/* Filtro status */}
      <div className="mb-3 flex gap-1">
        {STATUS_OPTS.map((o) => (
          <button
            key={o.value}
            type="button"
            onClick={() => { atualizarFiltro({ status: o.value || null }); }}
            className={`rounded px-3 py-1 text-sm border transition-colors ${
              (filters.status ?? "") === o.value
                ? "bg-gray-800 text-white border-gray-800"
                : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
            }`}
          >
            {o.label}
          </button>
        ))}
      </div>

      {/* Filtros */}
      <div className="mb-4 flex flex-wrap gap-3 text-sm">
        <div className="flex items-center gap-2">
          <label className="text-gray-500">De:</label>
          <input
            type="date"
            className="rounded border px-2 py-1 text-sm"
            value={filters.data_inicio ?? ""}
            onChange={(e) => atualizarFiltro({ data_inicio: e.target.value || null })}
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-gray-500">Até:</label>
          <input
            type="date"
            className="rounded border px-2 py-1 text-sm"
            value={filters.data_fim ?? ""}
            onChange={(e) => atualizarFiltro({ data_fim: e.target.value || null })}
          />
        </div>
        <select
          className="rounded border px-2 py-1 text-sm"
          value={filters.fornecedor_id ?? ""}
          onChange={(e) =>
            atualizarFiltro({ fornecedor_id: e.target.value ? Number(e.target.value) : null })
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
          {compras.map((compra) => {
            const expandido = expandidos.has(compra.id);
            return (
              <div key={compra.id} className={`rounded border ${compra.status === "cancelada" ? "text-gray-400" : ""}`}>
                <div className="flex items-center justify-between p-3">
                  <div className="flex items-start gap-2">
                    <button
                      type="button"
                      onClick={() => toggleExpandir(compra.id)}
                      className="mt-0.5 shrink-0 text-gray-400 hover:text-gray-700"
                      aria-label={expandido ? "Recolher itens" : "Expandir itens"}
                    >
                      {expandido ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    </button>
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
                {expandido && compra.itens.length > 0 && (
                  <div className="border-t mx-3 mb-3 pt-2">
                    <table className="w-full text-xs text-gray-600">
                      <thead>
                        <tr className="text-gray-400 border-b">
                          <th className="text-left pb-1 font-normal">Item</th>
                          <th className="text-right pb-1 font-normal">Qtd</th>
                          <th className="text-right pb-1 font-normal">Custo unit.</th>
                          <th className="text-right pb-1 font-normal">Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {compra.itens.map((item) => (
                          <tr key={item.item_id} className="border-b last:border-0">
                            <td className="py-1">{item.item_nome}</td>
                            <td className="py-1 text-right">{Number(item.quantidade)}</td>
                            <td className="py-1 text-right">{formatCurrency(item.custo_unitario)}</td>
                            <td className="py-1 text-right">{formatCurrency(item.custo_total)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="flex-1" />
      {compras.length > 0 && (
        <div className="sticky bottom-0 bg-white border-t border-gray-100 mt-4 py-2 flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPagina((p) => Math.max(1, p - 1))}
              disabled={pagina === 1}
            >
              ← Anterior
            </Button>
            <span>Página {pagina} de {totalPaginas}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPagina((p) => Math.min(totalPaginas, p + 1))}
              disabled={pagina === totalPaginas}
            >
              Próxima →
            </Button>
          </div>
          <div>
            Total no período: <span className="font-semibold text-gray-800">{formatCurrency(totalPeriodo)}</span>
          </div>
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

      <Dialog open={!!editando} onOpenChange={(v) => !v && setEditando(null)}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Editar Compra #{String(editando?.id ?? 0).padStart(4, "0")}</DialogTitle>
          </DialogHeader>
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
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditando(null)}>Cancelar</Button>
            <Button
              onClick={() => {
                if (!editando) return;
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
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
