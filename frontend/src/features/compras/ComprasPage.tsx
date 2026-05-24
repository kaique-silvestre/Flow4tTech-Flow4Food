import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useFornecedores } from "@/features/cadastros/fornecedores/useFornecedores";
import { formatCurrency } from "@/lib/format";
import {
  useCancelarCompra,
  useCompras,
  useConfirmarRecebimento,
  usePatchCompra,
  type CompraFilters,
  type CompraResponse,
} from "./useCompras";
import { ChevronRight, ChevronDown } from "lucide-react";

const STATUS_OPTS = [
  { value: "confirmado", label: "Agendadas" },
  { value: "recebido", label: "Recebidas" },
  { value: "", label: "Todas" },
  { value: "cancelado", label: "Canceladas" },
] as const;

const TIPO_LABELS: Record<string, string> = {
  imediata: "Imediata",
  agendada: "Agendada",
  a_prazo: "A prazo",
};

const STATUS_BADGE: Record<string, { label: string; cls: string }> = {
  confirmado: { label: "Aguardando entrega", cls: "bg-blue-100 text-blue-700" },
  recebido: { label: "Recebida", cls: "bg-green-100 text-green-700" },
  pago: { label: "Paga", cls: "bg-gray-100 text-gray-600" },
  cancelado: { label: "Cancelada", cls: "bg-gray-100 text-gray-400" },
};

function fmtDate(d: string | null | undefined) {
  if (!d) return "—";
  return new Date(d + "T00:00:00").toLocaleDateString("pt-BR");
}

export function ComprasPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<CompraFilters>({ status: "recebido" });
  const [pagina, setPagina] = useState(1);
  const { data: paginado, isLoading } = useCompras({ ...filters, pagina, por_pagina: 8 });
  const compras = paginado?.itens ?? [];
  const totalPaginas = paginado?.total_paginas ?? 1;

  function atualizarFiltro(update: Partial<CompraFilters>) {
    setFilters((f) => ({ ...f, ...update }));
    setPagina(1);
  }
  const { data: fornecedoresData } = useFornecedores();
  const fornecedores = fornecedoresData?.itens ?? [];
  const cancelarMutation = useCancelarCompra();
  const confirmarMutation = useConfirmarRecebimento();
  const patchMutation = usePatchCompra();

  const [expandidos, setExpandidos] = useState<Set<number>>(new Set());
  const [cancelando, setCancelando] = useState<CompraResponse | null>(null);
  const [confirmandoEntrega, setConfirmandoEntrega] = useState<CompraResponse | null>(null);
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
  const [editDataPrevReceb, setEditDataPrevReceb] = useState<string>("");
  const [editDataPrevPag, setEditDataPrevPag] = useState<string>("");

  const totalPeriodo = paginado?.total_periodo ?? 0;
  const statusSelecionado = filters.status ?? "";

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
              statusSelecionado === o.value
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
            const badge = STATUS_BADGE[compra.status];
            const isCancelado = compra.status === "cancelado";
            const isConfirmado = compra.status === "confirmado";
            return (
              <div key={compra.id} className={`rounded border ${isCancelado ? "opacity-60" : ""}`}>
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
                      <div className="font-medium flex flex-wrap items-center gap-2">
                        <span className="text-gray-400 font-normal">#{String(compra.id).padStart(4, "0")}</span>
                        {fmtDate(compra.data_compra)}
                        {" · "}
                        <span className="text-gray-600">{compra.fornecedor_nome ?? "Sem fornecedor"}</span>
                        {badge && (
                          <span className={`rounded-full px-2 py-0.5 text-xs ${badge.cls}`}>{badge.label}</span>
                        )}
                        <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                          {TIPO_LABELS[compra.tipo_compra] ?? compra.tipo_compra}
                        </span>
                      </div>
                      <div className="text-xs text-gray-400 flex flex-wrap gap-2">
                        <span>Nota: {compra.numero_nota ?? "—"} · {compra.itens.length} {compra.itens.length === 1 ? "item" : "itens"}</span>
                        {compra.data_prevista_recebimento && (
                          <span>Entrega prev.: {fmtDate(compra.data_prevista_recebimento)}</span>
                        )}
                        {compra.data_prevista_pagamento && (
                          <span>Venc. pag.: {fmtDate(compra.data_prevista_pagamento)}</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-right">
                    <div className={`font-semibold ${isCancelado ? "line-through" : ""}`}>{formatCurrency(compra.total)}</div>
                    {isConfirmado && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-green-600 text-green-700 hover:bg-green-50"
                          onClick={() => setConfirmandoEntrega(compra)}
                        >
                          Confirmar Entrega
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => {
                          setEditando(compra);
                          setEditFornecedorId(compra.fornecedor_id ? String(compra.fornecedor_id) : "");
                          setEditDataCompra(compra.data_compra);
                          setEditNumeroNota(compra.numero_nota ?? "");
                          setEditDataPrevReceb(compra.data_prevista_recebimento ?? "");
                          setEditDataPrevPag(compra.data_prevista_pagamento ?? "");
                        }}>
                          Editar
                        </Button>
                        <Button size="sm" variant="destructive" onClick={() => setCancelando(compra)}>
                          Cancelar
                        </Button>
                      </>
                    )}
                    {compra.status === "recebido" && (
                      <Button size="sm" variant="destructive" onClick={() => setCancelando(compra)}>
                        Cancelar Nota
                      </Button>
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
        open={!!confirmandoEntrega}
        title="Confirmar recebimento?"
        description={`Confirma que a compra #${String(confirmandoEntrega?.id ?? 0).padStart(4, "0")} foi entregue? O estoque será atualizado agora.`}
        confirmLabel="Confirmar Entrega"
        onConfirm={() => {
          if (confirmandoEntrega)
            confirmarMutation.mutate(confirmandoEntrega.id, { onSuccess: () => setConfirmandoEntrega(null) });
        }}
        onCancel={() => setConfirmandoEntrega(null)}
      />

      <ConfirmDialog
        open={!!cancelando}
        title="Cancelar nota fiscal?"
        description={`A nota #${String(cancelando?.id ?? 0).padStart(4, "0")} será cancelada${cancelando?.status === "recebido" ? " e o estoque será revertido" : ""}.`}
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
              <Input type="date" value={editDataCompra} onChange={(e) => setEditDataCompra(e.target.value)} />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-600">Número da Nota</label>
              <Input value={editNumeroNota} onChange={(e) => setEditNumeroNota(e.target.value)} placeholder="Opcional" />
            </div>
            {editando?.tipo_compra === "agendada" && (
              <div>
                <label className="mb-1 block text-sm text-gray-600">Data prevista de recebimento</label>
                <Input type="date" value={editDataPrevReceb} onChange={(e) => setEditDataPrevReceb(e.target.value)} />
              </div>
            )}
            {editando?.tipo_compra !== "imediata" && (
              <div>
                <label className="mb-1 block text-sm text-gray-600">Vencimento do pagamento</label>
                <Input type="date" value={editDataPrevPag} onChange={(e) => setEditDataPrevPag(e.target.value)} />
              </div>
            )}
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
                      data_prevista_recebimento: editDataPrevReceb || null,
                      data_prevista_pagamento: editDataPrevPag || null,
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
