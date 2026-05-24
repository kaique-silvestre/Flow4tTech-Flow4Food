import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useFornecedores } from "@/features/cadastros/fornecedores/useFornecedores";
import { formatCurrency } from "@/lib/format";
import {
  useContasPagar,
  usePagarConta,
  type ContaFilters,
  type ContaPagarResponse,
} from "./useContasPagar";

const STATUS_OPTS = [
  { value: "", label: "Todas" },
  { value: "pendente", label: "Pendentes" },
  { value: "vencido", label: "Vencidas" },
  { value: "pago", label: "Pagas" },
  { value: "cancelado", label: "Canceladas" },
] as const;

const STATUS_BADGE: Record<string, { label: string; cls: string }> = {
  pendente: { label: "Pendente", cls: "bg-yellow-100 text-yellow-700" },
  vencido: { label: "Vencida", cls: "bg-red-100 text-red-700" },
  pago: { label: "Paga", cls: "bg-green-100 text-green-700" },
  cancelado: { label: "Cancelada", cls: "bg-gray-100 text-gray-400" },
};

function fmtDate(d: string | null | undefined) {
  if (!d) return "—";
  return new Date(d + "T00:00:00").toLocaleDateString("pt-BR");
}

export function ContasPagarPage() {
  const [filters, setFilters] = useState<ContaFilters>({ status: "pendente" });
  const [pagina, setPagina] = useState(1);
  const { data: paginado, isLoading } = useContasPagar({ ...filters, pagina, por_pagina: 20 });
  const contas = paginado?.itens ?? [];
  const totalPaginas = paginado?.total_paginas ?? 1;

  const { data: fornecedoresData } = useFornecedores();
  const fornecedores = fornecedoresData?.itens ?? [];
  const pagarMutation = usePagarConta();

  const [pagando, setPagando] = useState<ContaPagarResponse | null>(null);
  const [dataPag, setDataPag] = useState<string>("");

  function atualizarFiltro(update: Partial<ContaFilters>) {
    setFilters((f) => ({ ...f, ...update }));
    setPagina(1);
  }

  const today = new Date().toISOString().split("T")[0];
  const statusSelecionado = filters.status ?? "";

  return (
    <div className="p-6 min-h-full flex flex-col">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Contas a Pagar</h1>
      </div>

      {paginado && (
        <div className="mb-4 flex gap-4">
          <div className="rounded border bg-yellow-50 px-4 py-2 text-sm">
            <div className="text-gray-500">Pendente</div>
            <div className="font-semibold text-yellow-700">{formatCurrency(paginado.total_pendente)}</div>
          </div>
          <div className="rounded border bg-red-50 px-4 py-2 text-sm">
            <div className="text-gray-500">Vencido</div>
            <div className="font-semibold text-red-700">{formatCurrency(paginado.total_vencido)}</div>
          </div>
        </div>
      )}

      {/* Filtro status */}
      <div className="mb-3 flex gap-1">
        {STATUS_OPTS.map((o) => (
          <button
            key={o.value}
            type="button"
            onClick={() => atualizarFiltro({ status: o.value || null })}
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
          <label className="text-gray-500">Venc. de:</label>
          <input
            type="date"
            className="rounded border px-2 py-1 text-sm"
            value={filters.data_vencimento_inicio ?? ""}
            onChange={(e) => atualizarFiltro({ data_vencimento_inicio: e.target.value || null })}
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-gray-500">Até:</label>
          <input
            type="date"
            className="rounded border px-2 py-1 text-sm"
            value={filters.data_vencimento_fim ?? ""}
            onChange={(e) => atualizarFiltro({ data_vencimento_fim: e.target.value || null })}
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
      ) : contas.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhuma conta encontrada.</p>
      ) : (
        <div className="space-y-2">
          {contas.map((conta) => {
            const badge = STATUS_BADGE[conta.status];
            const podeApagar = conta.status === "pendente" || conta.status === "vencido";
            return (
              <div key={conta.id} className={`flex items-center justify-between rounded border p-3 ${conta.status === "cancelado" ? "opacity-60" : ""}`}>
                <div>
                  <div className="font-medium flex items-center gap-2 flex-wrap">
                    <span className="text-gray-400 font-normal text-sm">#{String(conta.id).padStart(4, "0")}</span>
                    <span>{conta.fornecedor_nome ?? "Sem fornecedor"}</span>
                    {badge && (
                      <span className={`rounded-full px-2 py-0.5 text-xs ${badge.cls}`}>{badge.label}</span>
                    )}
                  </div>
                  <div className="text-xs text-gray-400 flex gap-3 mt-0.5">
                    <span>Vencimento: {fmtDate(conta.data_vencimento)}</span>
                    {conta.data_pagamento && <span>Pago em: {fmtDate(conta.data_pagamento)}</span>}
                    {conta.compra_id && <span>Compra #{String(conta.compra_id).padStart(4, "0")}</span>}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className={`font-semibold ${conta.status === "vencido" ? "text-red-600" : ""}`}>
                    {formatCurrency(conta.valor)}
                  </div>
                  {podeApagar && (
                    <Button
                      size="sm"
                      onClick={() => {
                        setPagando(conta);
                        setDataPag(today);
                      }}
                    >
                      Registrar Pagamento
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="flex-1" />
      {totalPaginas > 1 && (
        <div className="sticky bottom-0 bg-white border-t border-gray-100 mt-4 py-2 flex items-center gap-2 text-sm text-gray-500">
          <Button variant="outline" size="sm" onClick={() => setPagina((p) => Math.max(1, p - 1))} disabled={pagina === 1}>
            ← Anterior
          </Button>
          <span>Página {pagina} de {totalPaginas}</span>
          <Button variant="outline" size="sm" onClick={() => setPagina((p) => Math.min(totalPaginas, p + 1))} disabled={pagina === totalPaginas}>
            Próxima →
          </Button>
        </div>
      )}

      {/* Modal pagamento */}
      <Dialog open={!!pagando} onOpenChange={(v) => !v && setPagando(null)}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Registrar Pagamento</DialogTitle>
          </DialogHeader>
          {pagando && (
            <div className="space-y-3">
              <div className="rounded bg-gray-50 p-2 text-sm text-gray-600">
                <div>{pagando.fornecedor_nome ?? "Sem fornecedor"}</div>
                <div className="font-semibold">{formatCurrency(pagando.valor)}</div>
                <div className="text-xs text-gray-400">Venc.: {fmtDate(pagando.data_vencimento)}</div>
              </div>
              <div className="space-y-1">
                <Label>Data do pagamento</Label>
                <Input type="date" value={dataPag} onChange={(e) => setDataPag(e.target.value)} />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setPagando(null)}>Cancelar</Button>
            <Button
              disabled={!dataPag || pagarMutation.isPending}
              onClick={() => {
                if (!pagando || !dataPag) return;
                pagarMutation.mutate(
                  { id: pagando.id, data: { data_pagamento: dataPag } },
                  { onSuccess: () => setPagando(null) },
                );
              }}
            >
              {pagarMutation.isPending ? "Salvando..." : "Confirmar Pagamento"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
