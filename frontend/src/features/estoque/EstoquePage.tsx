import { useState } from "react";
import { useDebounce } from "use-debounce";
import { Button } from "@/components/ui/button";
import { Pagination, paginar } from "@/components/ui/pagination";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { useCategorias } from "@/features/cadastros/categorias/useCategorias";
import { formatCurrency, formatCustoMedio, stockDisplay } from "@/lib/format";
import { BaixaSemVendaModal } from "./BaixaSemVendaModal";
import { useSaldoEstoque, type SaldoFilters } from "./useEstoque";

const POR_PAGINA = 20;

export function EstoquePage() {
  const [filters, setFilters] = useState<SaldoFilters>({});
  const [debouncedBusca] = useDebounce(filters.busca, 350);
  const queryFilters: SaldoFilters = { ...filters, busca: filters.busca === "" || filters.busca == null ? filters.busca : debouncedBusca };
  const { data: saldoData, isLoading, isError } = useSaldoEstoque(queryFilters);
  const itens = saldoData?.itens ?? [];
  const { data: categorias = [] } = useCategorias();
  const [baixaOpen, setBaixaOpen] = useState(false);
  const [pagina, setPagina] = useState(1);

  return (
    <div className="p-6 min-h-full flex flex-col">
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
          onChange={(e) => { setFilters((f) => ({ ...f, busca: e.target.value || null })); setPagina(1); }}
        />
      </div>

      {/* Tabela */}
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />)}
        </div>
      ) : isError ? (
        <p className="text-sm text-red-500">Erro ao carregar estoque. Tente novamente.</p>
      ) : itens.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum item em estoque.</p>
      ) : (
        <div className="flex-1 flex flex-col">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Item</TableHead>
                <TableHead>Categoria</TableHead>
                <TableHead className="text-right">Estoque atual</TableHead>
                <TableHead className="text-right">Reservado</TableHead>
                <TableHead className="text-right">Disponível</TableHead>
                <TableHead className="text-right">Custo médio</TableHead>
                <TableHead className="text-right">Valor em estoque</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginar(itens, pagina, POR_PAGINA).map((item) => {
                const valorEstoque =
                  item.custo_medio != null
                    ? Number(item.estoque_atual) * item.custo_medio
                    : null;
                const { qty, unit } = stockDisplay(item.estoque_atual, item.unidade_base);
                const isCritico = item.nivel_critico != null && item.nivel_critico > 0 && Number(item.estoque_disponivel) < Number(item.nivel_critico);
                return (
                  <TableRow key={item.id} className={isCritico ? "bg-orange-50" : undefined}>
                    <TableCell className="font-medium">
                      <span className="inline-flex items-center gap-2">
                        {isCritico && (
                          <span className="relative flex h-2.5 w-2.5 flex-shrink-0">
                            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
                            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-red-500" />
                          </span>
                        )}
                        {item.nome}
                      </span>
                    </TableCell>
                    <TableCell className="text-gray-500">{item.categoria_nome ?? "—"}</TableCell>
                    <TableCell className={`text-right font-medium ${Number(item.estoque_atual) < 0 ? "text-red-600" : isCritico ? "text-orange-600" : ""}`}>
                      {qty} {unit}
                    </TableCell>
                    <TableCell className="text-right text-gray-500">
                      {stockDisplay(item.estoque_reservado, item.unidade_base).qty} {stockDisplay(item.estoque_reservado, item.unidade_base).unit}
                    </TableCell>
                    <TableCell className={`text-right font-medium ${Number(item.estoque_disponivel) < 0 ? "text-red-600" : ""}`}>
                      {stockDisplay(item.estoque_disponivel, item.unidade_base).qty} {stockDisplay(item.estoque_disponivel, item.unidade_base).unit}
                    </TableCell>
                    <TableCell className="text-right text-gray-600">
                      {formatCustoMedio(item.custo_medio, item.unidade_base)}
                    </TableCell>
                    <TableCell className="text-right text-gray-600">
                      {valorEstoque != null ? formatCurrency(valorEstoque) : "—"}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
          <div className="border-t border-gray-100">
            <div className="flex items-center justify-between py-2 text-sm font-medium text-gray-700">
              <span>Total em estoque</span>
              <span className="text-gray-900">
                {formatCurrency(
                  itens.reduce((sum, item) => {
                    if (item.custo_medio == null) return sum;
                    return sum + Number(item.estoque_atual) * item.custo_medio;
                  }, 0)
                )}
              </span>
            </div>
            <Pagination
              pagina={pagina}
              totalPaginas={Math.ceil(itens.length / POR_PAGINA)}
              total={itens.length}
              label="itens"
              onPageChange={setPagina}
            />
          </div>
        </div>
      )}

      <BaixaSemVendaModal open={baixaOpen} onClose={() => setBaixaOpen(false)} itens={itens} />
    </div>
  );
}
