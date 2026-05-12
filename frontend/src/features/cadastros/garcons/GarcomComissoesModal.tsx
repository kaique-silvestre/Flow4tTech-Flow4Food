import { useState } from "react";
import { Button } from "@/components/ui/button";
import { paginar } from "@/components/ui/pagination";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { formatCurrency } from "@/lib/format";
import type { Garcom, ComissaoResponse } from "./useGarcons";
import {
  useGarcomStats,
  useUpdateComissao,
  useTogglePagoComissao,
  useDeleteComissao,
} from "./useGarcons";

interface Props {
  open: boolean;
  onClose: () => void;
  garcom: Garcom;
}

function ComissaoRow({ c, onUpdated }: { c: ComissaoResponse; onUpdated: () => void }) {
  const [editingValor, setEditingValor] = useState<string | null>(null);
  const updateComissao = useUpdateComissao();
  const togglePago = useTogglePagoComissao();
  const deleteComissao = useDeleteComissao();

  function handleValorBlur() {
    if (editingValor === null) return;
    const parsed = parseFloat(editingValor);
    if (!isNaN(parsed) && parsed > 0 && parsed !== Number(c.valor)) {
      updateComissao.mutate({ id: c.id, valor: parsed }, { onSuccess: onUpdated });
    }
    setEditingValor(null);
  }

  return (
    <tr className="border-b last:border-0 text-sm">
      <td className="py-2 pr-3 text-gray-600">#{c.comanda_id}</td>
      <td className="py-2 pr-3 text-gray-600">
        {new Date(c.created_at).toLocaleDateString("pt-BR")}
      </td>
      <td className="py-2 pr-3">
        {editingValor !== null ? (
          <Input
            type="number"
            step="0.01"
            min="0.01"
            className="w-24 h-7 text-sm"
            value={editingValor}
            onChange={(e) => setEditingValor(e.target.value)}
            onBlur={handleValorBlur}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleValorBlur();
              if (e.key === "Escape") setEditingValor(null);
            }}
            autoFocus
          />
        ) : (
          <button
            className="hover:underline text-left"
            onClick={() => setEditingValor(Number(c.valor).toFixed(2))}
            title="Clique para editar"
          >
            {formatCurrency(Number(c.valor))}
          </button>
        )}
      </td>
      <td className="py-2 pr-3">
        <button
          onClick={() => togglePago.mutate(c.id, { onSuccess: onUpdated })}
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
            c.pago
              ? "bg-green-100 text-green-700 hover:bg-green-200"
              : "bg-yellow-100 text-yellow-700 hover:bg-yellow-200"
          }`}
        >
          {c.pago ? "Pago" : "Pendente"}
        </button>
      </td>
      <td className="py-2">
        <Button
          size="sm"
          variant="ghost"
          className="text-red-500 hover:text-red-700 h-7 px-2"
          onClick={() =>
            deleteComissao.mutate({ id: c.id, garcom_id: c.garcom_id }, { onSuccess: onUpdated })
          }
          disabled={deleteComissao.isPending}
        >
          Excluir
        </Button>
      </td>
    </tr>
  );
}

const COMISSOES_POR_PAGINA = 5;

export function GarcomComissoesModal({ open, onClose, garcom }: Props) {
  const { data: stats, isLoading, refetch } = useGarcomStats(open ? garcom.id : 0);
  const [pagina, setPagina] = useState(1);

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Comissões — {garcom.nome}</DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <div className="space-y-2 py-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-8 animate-pulse rounded bg-gray-100" />
            ))}
          </div>
        ) : stats ? (
          <div className="space-y-4">
            {/* Stats summary */}
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-lg border p-3 text-center">
                <p className="text-2xl font-bold">{stats.total_comandas}</p>
                <p className="text-xs text-gray-500">Comandas totais</p>
              </div>
              <div className="rounded-lg border p-3 text-center">
                <p className="text-2xl font-bold">{stats.comandas_fechadas}</p>
                <p className="text-xs text-gray-500">Fechadas</p>
              </div>
              <div className="rounded-lg border p-3 text-center">
                <p className="text-2xl font-bold text-amber-600">
                  {formatCurrency(Number(stats.comissao_pendente))}
                </p>
                <p className="text-xs text-gray-500">Comissão pendente</p>
              </div>
            </div>

            {/* Commissions table */}
            {stats.comissoes.length === 0 ? (
              <p className="text-sm text-gray-500 py-2">Nenhuma comissão registrada.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr className="border-b text-left text-gray-500">
                      <th className="py-2 pr-3">Comanda</th>
                      <th className="py-2 pr-3">Data</th>
                      <th className="py-2 pr-3">Valor</th>
                      <th className="py-2 pr-3">Status</th>
                      <th className="py-2" />
                    </tr>
                  </thead>
                  <tbody>
                    {paginar(stats.comissoes, pagina, COMISSOES_POR_PAGINA).map((c) => (
                      <ComissaoRow key={c.id} c={c} onUpdated={() => refetch()} />
                    ))}
                  </tbody>
                </table>
                {stats.comissoes.length > COMISSOES_POR_PAGINA && (
                  <div className="mt-3 flex items-center justify-between text-sm text-gray-500">
                    <span>{stats.comissoes.length} comissões</span>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setPagina((p) => Math.max(1, p - 1))}
                        disabled={pagina === 1}
                        className="rounded border px-2 py-0.5 disabled:opacity-40 hover:bg-gray-50"
                      >
                        ‹
                      </button>
                      <span>
                        {pagina} / {Math.ceil(stats.comissoes.length / COMISSOES_POR_PAGINA)}
                      </span>
                      <button
                        onClick={() => setPagina((p) => Math.min(Math.ceil(stats.comissoes.length / COMISSOES_POR_PAGINA), p + 1))}
                        disabled={pagina === Math.ceil(stats.comissoes.length / COMISSOES_POR_PAGINA)}
                        className="rounded border px-2 py-0.5 disabled:opacity-40 hover:bg-gray-50"
                      >
                        ›
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-500 py-4">Erro ao carregar dados.</p>
        )}

        <div className="flex justify-end pt-2">
          <Button variant="outline" onClick={onClose}>
            Fechar
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
