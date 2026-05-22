import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { formatCurrency } from "@/lib/format";
import { useProdutosMaisVendidos } from "./useRelatorios";

function diasAtras(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().split("T")[0];
}

function hoje(): string {
  return new Date().toISOString().split("T")[0];
}

const RANK_COLORS = ["text-yellow-500", "text-gray-400", "text-amber-600"];

export function ProdutosMaisVendidosPage() {
  const navigate = useNavigate();
  const [dataInicio, setDataInicio] = useState(() => diasAtras(30));
  const [dataFim, setDataFim] = useState(hoje);

  const { data, isLoading } = useProdutosMaisVendidos({ data_inicio: dataInicio, data_fim: dataFim });

  return (
    <div className="p-6">
      <button
        onClick={() => navigate("/relatorios")}
        className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800"
      >
        ← Relatórios
      </button>
      <h1 className="mb-6 text-xl font-semibold">Produtos Mais Vendidos</h1>

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

      {data && data.itens.length > 0 && (
        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-lg border bg-white p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Itens distintos</p>
            <p className="mt-1 text-2xl font-semibold">{data.itens.length}</p>
          </div>
          <div className="rounded-lg border bg-white p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Receita total (período)</p>
            <p className="mt-1 text-2xl font-semibold">{formatCurrency(data.receita_total_periodo)}</p>
          </div>
          <div className="rounded-lg border bg-white p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Produto #1</p>
            <p className="mt-1 text-lg font-semibold truncate">{data.itens[0].produto_nome}</p>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : !data ? null : data.itens.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhuma venda registrada no período.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-xs font-semibold uppercase text-gray-500">
              <th className="pb-2 w-10">#</th>
              <th className="pb-2">Produto</th>
              <th className="pb-2">Categoria</th>
              <th className="pb-2 text-right">Qtd vendida</th>
              <th className="pb-2 text-right">Receita</th>
              <th className="pb-2 text-right">% do total</th>
            </tr>
          </thead>
          <tbody>
            {data.itens.map((item, idx) => (
              <tr key={item.produto_id} className="border-b hover:bg-gray-50">
                <td className={`py-2 font-bold ${RANK_COLORS[idx] ?? "text-gray-400"}`}>
                  {idx + 1}
                </td>
                <td className="py-2 font-medium">{item.produto_nome}</td>
                <td className="py-2 text-gray-500">{item.categoria_nome ?? "—"}</td>
                <td className="py-2 text-right">
                  {Number(item.quantidade_total) % 1 === 0
                    ? Number(item.quantidade_total).toFixed(0)
                    : Number(item.quantidade_total).toFixed(2)}
                </td>
                <td className="py-2 text-right">{formatCurrency(item.receita_total)}</td>
                <td className="py-2 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <div className="h-1.5 w-16 rounded-full bg-gray-100 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-blue-500"
                        style={{ width: `${Math.min(item.percentual_receita, 100)}%` }}
                      />
                    </div>
                    <span className="w-10 text-right">{Number(item.percentual_receita).toFixed(1)}%</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t font-semibold">
              <td colSpan={4} className="pt-2 text-right text-gray-500">Total</td>
              <td className="pt-2 text-right">{formatCurrency(data.receita_total_periodo)}</td>
              <td className="pt-2 text-right">100%</td>
            </tr>
          </tfoot>
        </table>
      )}
    </div>
  );
}
