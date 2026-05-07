import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useCategorias } from "@/features/cadastros/categorias/useCategorias";
import { formatCurrency } from "@/lib/format";
import { BaixaSemVendaModal } from "./BaixaSemVendaModal";
import { useSaldoEstoque, type SaldoFilters } from "./useEstoque";

export function EstoquePage() {
  const [filters, setFilters] = useState<SaldoFilters>({});
  const { data: itens = [], isLoading } = useSaldoEstoque(filters);
  const { data: categorias = [] } = useCategorias();
  const [baixaOpen, setBaixaOpen] = useState(false);

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Estoque</h1>
        <Button onClick={() => setBaixaOpen(true)}>Baixa Sem Venda</Button>
      </div>

      {/* Filtros */}
      <div className="mb-4 flex flex-wrap gap-3 text-sm">
        <select
          className="rounded border px-2 py-1 text-sm"
          value={filters.categoria_id ?? ""}
          onChange={(e) =>
            setFilters((f) => ({ ...f, categoria_id: e.target.value ? Number(e.target.value) : null }))
          }
        >
          <option value="">Todas as categorias</option>
          {categorias.map((c) => (
            <option key={c.id} value={c.id}>{c.nome}</option>
          ))}
        </select>

        <input
          className="rounded border px-2 py-1 text-sm"
          placeholder="Buscar item..."
          value={filters.busca ?? ""}
          onChange={(e) => setFilters((f) => ({ ...f, busca: e.target.value || null }))}
        />
      </div>

      {/* Tabela */}
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />)}
        </div>
      ) : itens.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum item em estoque.</p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2 pr-4">Item</th>
              <th className="py-2 pr-4">Categoria</th>
              <th className="py-2 pr-4">Saldo</th>
              <th className="py-2">Custo médio</th>
            </tr>
          </thead>
          <tbody>
            {itens.map((item) => (
              <tr key={item.id} className="border-b last:border-0">
                <td className="py-2 pr-4 font-medium">{item.nome}</td>
                <td className="py-2 pr-4 text-gray-500">{item.categoria_nome ?? "—"}</td>
                <td className={`py-2 pr-4 font-medium ${Number(item.estoque_atual) < 0 ? "text-red-600" : ""}`}>
                  {Number(item.estoque_atual).toLocaleString("pt-BR")} {item.unidade_base}
                </td>
                <td className="py-2 text-gray-600">
                  {item.custo_medio != null
                    ? `${formatCurrency(item.custo_medio)}/${item.unidade_base}`
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <BaixaSemVendaModal open={baixaOpen} onClose={() => setBaixaOpen(false)} itens={itens} />
    </div>
  );
}
