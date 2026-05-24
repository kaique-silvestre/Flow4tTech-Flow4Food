import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { formatCurrency } from "@/lib/format";
import { useVendasPorProduto } from "./useRelatorios";

function diasAtras(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().split("T")[0];
}

function hoje(): string {
  return new Date().toISOString().split("T")[0];
}

export function VendasPorProdutoPage() {
  const navigate = useNavigate();
  const [dataInicio, setDataInicio] = useState(() => diasAtras(30));
  const [dataFim, setDataFim] = useState(hoje);

  const { data, isLoading } = useVendasPorProduto({ data_inicio: dataInicio, data_fim: dataFim });

  return (
    <div className="p-6">
      <button
        onClick={() => navigate("/relatorios")}
        className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800"
      >
        ← Relatórios
      </button>
      <h1 className="mb-6 text-xl font-semibold">Vendas por Produto</h1>

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
      ) : !data ? null : data.itens.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhuma venda registrada no período.</p>
      ) : (
        <>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-xs font-semibold uppercase text-gray-500">
                <th className="pb-2">#</th>
                <th className="pb-2">Produto</th>
                <th className="pb-2">Categoria</th>
                <th className="pb-2 text-right">Qtd vendida</th>
                <th className="pb-2 text-right">Cortesias</th>
                <th className="pb-2 text-right">Ticket médio</th>
                <th className="pb-2 text-right">Faturamento</th>
                <th className="pb-2 text-right">% total</th>
              </tr>
            </thead>
            <tbody>
              {data.itens.map((item, idx) => {
                const pct =
                  data.total_faturamento > 0
                    ? ((item.faturamento / data.total_faturamento) * 100).toFixed(1)
                    : "0.0";
                return (
                  <tr key={item.produto_id} className="border-b">
                    <td className="py-2 pr-3 text-gray-400">{idx + 1}</td>
                    <td className="py-2 pr-4 font-medium">{item.produto_nome}</td>
                    <td className="py-2 pr-4 text-gray-500">{item.categoria_nome ?? "—"}</td>
                    <td className="py-2 pr-4 text-right">{Number(item.qtd_vendida)}</td>
                    <td className="py-2 pr-4 text-right text-purple-600">
                      {Number(item.qtd_cortesias) > 0 ? Number(item.qtd_cortesias) : "—"}
                    </td>
                    <td className="py-2 pr-4 text-right text-gray-500">
                      {formatCurrency(item.ticket_medio)}
                    </td>
                    <td className="py-2 pr-4 text-right font-medium">
                      {formatCurrency(item.faturamento)}
                    </td>
                    <td className="py-2 text-right text-gray-500">{pct}%</td>
                  </tr>
                );
              })}
            </tbody>
            <tfoot>
              <tr className="border-t font-semibold">
                <td colSpan={6} className="pt-2 text-right text-gray-500">
                  Total
                </td>
                <td className="pt-2 text-right">{formatCurrency(data.total_faturamento)}</td>
                <td className="pt-2 text-right text-gray-500">100%</td>
              </tr>
            </tfoot>
          </table>
        </>
      )}
    </div>
  );
}
