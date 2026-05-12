import { useNavigate } from "react-router-dom";
import { formatCurrency } from "@/lib/format";
import { useCMVPorProduto } from "./useRelatorios";

const BADGE: Record<string, string> = {
  verde: "bg-green-100 text-green-800",
  amarelo: "bg-yellow-100 text-yellow-800",
  vermelho: "bg-red-100 text-red-800",
  sem_custo: "bg-gray-100 text-gray-500",
};

const LABEL: Record<string, string> = {
  verde: "Verde >40%",
  amarelo: "Amarelo 20-40%",
  vermelho: "Vermelho <20%",
  sem_custo: "Sem custo",
};

export function CmvPorProdutoPage() {
  const navigate = useNavigate();
  const { data, isLoading } = useCMVPorProduto();

  return (
    <div className="p-6">
      <button
        onClick={() => navigate("/relatorios")}
        className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800"
      >
        ← Relatórios
      </button>
      <h1 className="mb-6 text-xl font-semibold">CMV por Produto</h1>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : !data || data.itens.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum produto vendável cadastrado.</p>
      ) : (
        <>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-xs font-semibold uppercase text-gray-500">
                <th className="pb-2">Produto</th>
                <th className="pb-2 text-right">Preço Venda</th>
                <th className="pb-2 text-right">Custo Médio</th>
                <th className="pb-2 text-right">Margem R$</th>
                <th className="pb-2 text-right">Margem %</th>
                <th className="pb-2 text-center">Classificação</th>
              </tr>
            </thead>
            <tbody>
              {data.itens.map((item) => (
                <tr key={item.item_id} className="border-b">
                  <td className="py-2">{item.nome}</td>
                  <td className="py-2 text-right">
                    {item.preco_venda != null ? formatCurrency(item.preco_venda) : "—"}
                  </td>
                  <td className="py-2 text-right">
                    {item.custo_medio != null ? formatCurrency(item.custo_medio) : "—"}
                  </td>
                  <td className="py-2 text-right">
                    {item.margem_valor != null ? formatCurrency(item.margem_valor) : "—"}
                  </td>
                  <td className="py-2 text-right">
                    {item.margem_percentual != null
                      ? `${Number(item.margem_percentual).toFixed(1)}%`
                      : "—"}
                  </td>
                  <td className="py-2 text-center">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${BADGE[item.classificacao]}`}
                    >
                      {LABEL[item.classificacao]}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="mt-4 flex gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <span className="inline-block h-3 w-3 rounded-full bg-green-400" /> Verde: margem &gt; 40%
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-3 w-3 rounded-full bg-yellow-400" /> Amarelo: 20–40%
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-3 w-3 rounded-full bg-red-400" /> Vermelho: &lt; 20%
            </span>
          </div>
        </>
      )}
    </div>
  );
}
