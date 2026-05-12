import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { formatCurrency } from "@/lib/format";
import { useVendasPorGarcom } from "./useRelatorios";

function diasAtras(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().split("T")[0];
}

function hoje(): string {
  return new Date().toISOString().split("T")[0];
}

export function VendasPorGarcomPage() {
  const navigate = useNavigate();
  const [dataInicio, setDataInicio] = useState(() => diasAtras(30));
  const [dataFim, setDataFim] = useState(hoje);

  const { data, isLoading } = useVendasPorGarcom({
    data_inicio: dataInicio,
    data_fim: dataFim,
  });

  const totalFaturamento = data?.garcons.reduce((acc, g) => acc + g.faturamento, 0) ?? 0;
  const totalComissoes = data?.garcons.reduce((acc, g) => acc + g.comissao, 0) ?? 0;

  return (
    <div className="p-6">
      <button
        onClick={() => navigate("/relatorios")}
        className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800"
      >
        ← Relatórios
      </button>
      <h1 className="mb-6 text-xl font-semibold">Vendas por Garçom</h1>

      <div className="mb-6 flex flex-wrap gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500">De</label>
          <input
            type="date"
            value={dataInicio}
            onChange={(e) => setDataInicio(e.target.value)}
            className="rounded border px-2 py-1 text-sm"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500">Até</label>
          <input
            type="date"
            value={dataFim}
            onChange={(e) => setDataFim(e.target.value)}
            className="rounded border px-2 py-1 text-sm"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : !data ? null : data.garcons.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhuma venda registrada no período.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-xs font-semibold uppercase text-gray-500">
              <th className="pb-2">#</th>
              <th className="pb-2">Garçom</th>
              <th className="pb-2 text-right">Comandas</th>
              <th className="pb-2 text-right">Faturamento</th>
              <th className="pb-2 text-right">Ticket Médio</th>
              <th className="pb-2 text-right">Comissão (a pagar)</th>
            </tr>
          </thead>
          <tbody>
            {data.garcons.map((g, idx) => (
              <tr key={g.garcom_id} className="border-b">
                <td className="py-2 text-gray-400">{idx + 1}</td>
                <td className="py-2 font-medium">{g.garcom_nome}</td>
                <td className="py-2 text-right">{g.qtd_comandas}</td>
                <td className="py-2 text-right">{formatCurrency(g.faturamento)}</td>
                <td className="py-2 text-right">{formatCurrency(g.ticket_medio)}</td>
                <td className="py-2 text-right text-blue-600">{formatCurrency(g.comissao)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t font-semibold">
              <td colSpan={3} className="pt-2 text-right text-gray-500">
                Total
              </td>
              <td className="pt-2 text-right">{formatCurrency(totalFaturamento)}</td>
              <td />
              <td className="pt-2 text-right text-blue-600">{formatCurrency(totalComissoes)}</td>
            </tr>
          </tfoot>
        </table>
      )}
    </div>
  );
}
