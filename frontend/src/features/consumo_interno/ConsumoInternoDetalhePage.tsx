import { useState } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { formatCurrency, formatQuantidade } from "@/lib/format";
import { useItensConsumo, useEstornarConsumo } from "./useConsumoInterno";
import { LancarConsumoModal } from "./LancarConsumoModal";

const MESES = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

function currentMonth() {
  const now = new Date();
  return { mes: now.getMonth() + 1, ano: now.getFullYear() };
}

import { parseApiDate } from "@/lib/format";

const fmtData = (iso: string) =>
  parseApiDate(iso).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });

export function ConsumoInternoDetalhePage() {
  const { consumidorId } = useParams<{ consumidorId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const initialMes = searchParams.get("mes") ? Number(searchParams.get("mes")) : currentMonth().mes;
  const initialAno = searchParams.get("ano") ? Number(searchParams.get("ano")) : currentMonth().ano;
  const [periodo, setPeriodo] = useState({ mes: initialMes, ano: initialAno });

  const cId = Number(consumidorId);
  const { data: itens = [], isLoading } = useItensConsumo({
    consumidor_id: cId,
    mes: periodo.mes,
    ano: periodo.ano,
  });


  const [showModal, setShowModal] = useState(false);
  const [estornoId, setEstornoId] = useState<number | null>(null);
  const estornar = useEstornarConsumo();

  const total = itens.reduce((acc, i) => acc + Number(i.subtotal), 0);
  const consumidorNome = itens.length > 0 ? itens[0].consumidor_nome : `Consumidor #${cId}`;

  function changeMes(delta: number) {
    setPeriodo((p) => {
      let m = p.mes + delta;
      let a = p.ano;
      if (m < 1) { m = 12; a--; }
      if (m > 12) { m = 1; a++; }
      return { mes: m, ano: a };
    });
  }

  function handleEstornar() {
    if (estornoId == null) return;
    estornar.mutate(estornoId, { onSuccess: () => setEstornoId(null) });
  }

  return (
    <div className="p-4 lg:p-6">
      {/* Header */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate("/consumo-interno")}
            className="flex h-9 w-9 items-center justify-center rounded border text-gray-600 hover:bg-gray-50"
          >
            <ArrowLeft size={18} />
          </button>
          <h1 className="text-xl font-semibold">{consumidorNome}</h1>
        </div>
        <Button onClick={() => setShowModal(true)}>+ Lançar Consumo</Button>
      </div>

      {/* Seletor de mês/ano */}
      <div className="mb-4 flex items-center gap-3">
        <button
          onClick={() => changeMes(-1)}
          className="flex h-9 w-9 items-center justify-center rounded border text-gray-600 hover:bg-gray-50"
        >
          ◀
        </button>
        <span className="min-w-[160px] text-center font-medium">
          {MESES[periodo.mes - 1]} {periodo.ano}
        </span>
        <button
          onClick={() => changeMes(1)}
          className="flex h-9 w-9 items-center justify-center rounded border text-gray-600 hover:bg-gray-50"
        >
          ▶
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-14 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : itens.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum consumo registrado neste período.</p>
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden sm:block overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="pb-2 font-medium">Item</th>
                  <th className="pb-2 font-medium text-center">Qtd</th>
                  <th className="pb-2 font-medium text-right">Custo unit.</th>
                  <th className="pb-2 font-medium text-right">Subtotal</th>
                  <th className="pb-2 font-medium text-right">Data</th>
                  <th className="pb-2 font-medium text-right">Ações</th>
                </tr>
              </thead>
              <tbody>
                {itens.map((item) => (
                  <tr key={item.id} className="border-b">
                    <td className="py-3">
                      <div className="font-medium">{item.produto_nome}</div>
                      {item.observacao && (
                        <div className="text-xs text-gray-400">{item.observacao}</div>
                      )}
                    </td>
                    <td className="py-3 text-center">{formatQuantidade(item.quantidade)}</td>
                    <td className="py-3 text-right">{formatCurrency(Number(item.custo_unitario))}</td>
                    <td className="py-3 text-right font-medium">{formatCurrency(Number(item.subtotal))}</td>
                    <td className="py-3 text-right text-gray-500">{fmtData(item.created_at)}</td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => setEstornoId(item.id)}
                        className="text-xs text-red-600 hover:underline"
                      >
                        Estornar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t-2">
                  <td colSpan={3} className="pt-3 font-semibold">Total</td>
                  <td className="pt-3 text-right font-semibold">{formatCurrency(total)}</td>
                  <td colSpan={2} />
                </tr>
              </tfoot>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="space-y-2 sm:hidden">
            {itens.map((item) => (
              <div key={item.id} className="rounded border p-3">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-medium">{item.produto_nome}</div>
                    {item.observacao && (
                      <div className="text-xs text-gray-400">{item.observacao}</div>
                    )}
                    <div className="mt-1 text-xs text-gray-500">
                      {formatQuantidade(item.quantidade)} × {formatCurrency(Number(item.custo_unitario))} · {fmtData(item.created_at)}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">{formatCurrency(Number(item.subtotal))}</div>
                    <button
                      onClick={() => setEstornoId(item.id)}
                      className="mt-1 text-xs text-red-600 hover:underline"
                    >
                      Estornar
                    </button>
                  </div>
                </div>
              </div>
            ))}
            <div className="rounded bg-gray-50 p-3 text-right font-semibold">
              Total: {formatCurrency(total)}
            </div>
          </div>
        </>
      )}

      {/* Total em destaque */}
      {itens.length > 0 && (
        <div className="mt-4 hidden sm:flex justify-end">
          <div className="rounded-lg bg-gray-50 px-6 py-3 text-right">
            <div className="text-sm text-gray-500">Total acumulado</div>
            <div className="text-2xl font-bold">{formatCurrency(total)}</div>
          </div>
        </div>
      )}

      <LancarConsumoModal
        open={showModal}
        consumidorId={cId}
        onClose={() => setShowModal(false)}
      />

      <ConfirmDialog
        open={estornoId != null}
        title="Estornar consumo"
        description="O estoque será devolvido e o registro removido. Deseja continuar?"
        confirmLabel="Estornar"
        onConfirm={handleEstornar}
        onCancel={() => setEstornoId(null)}
        isPending={estornar.isPending}
      />
    </div>
  );
}
