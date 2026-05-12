import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useSaldoEstoque } from "./useEstoque";
import { useMovimentos, type MovimentoFilters } from "./useEstoque";

const TIPO_OPTIONS = [
  { value: "", label: "Todos os tipos" },
  { value: "entrada", label: "Entrada" },
  { value: "saida_venda", label: "Saída venda" },
  { value: "saida_perda", label: "Baixa" },
  { value: "estorno_compra", label: "Estorno compra" },
];

const TIPO_BADGE: Record<string, string> = {
  entrada: "bg-green-100 text-green-700",
  saida_venda: "bg-blue-100 text-blue-700",
  saida_perda: "bg-orange-100 text-orange-700",
  estorno_compra: "bg-gray-100 text-gray-500",
};

const TIPO_LABEL: Record<string, string> = {
  entrada: "Entrada",
  saida_venda: "Saída venda",
  saida_perda: "Baixa",
  estorno_compra: "Estorno compra",
};

export function MovimentosPage() {
  const [filters, setFilters] = useState<MovimentoFilters>({ pagina: 1, por_pagina: 50 });
  const { data: result, isLoading } = useMovimentos(filters);
  const { data: itens = [] } = useSaldoEstoque();

  const totalPaginas = result ? Math.ceil(result.total / (filters.por_pagina ?? 50)) : 1;

  function setPage(p: number) {
    setFilters((f) => ({ ...f, pagina: p }));
  }

  return (
    <div className="p-6">
      <div className="mb-4">
        <h1 className="text-xl font-semibold">Histórico de Movimentações</h1>
      </div>

      {/* Filtros */}
      <div className="mb-4 flex flex-wrap gap-3 text-sm">
        <select
          className="rounded border px-2 py-1 text-sm"
          value={filters.item_id ?? ""}
          onChange={(e) =>
            setFilters((f) => ({ ...f, item_id: e.target.value ? Number(e.target.value) : null, pagina: 1 }))
          }
        >
          <option value="">Todos os itens</option>
          {itens.map((i) => (
            <option key={i.id} value={i.id}>{i.nome}</option>
          ))}
        </select>

        <select
          className="rounded border px-2 py-1 text-sm"
          value={filters.tipo ?? ""}
          onChange={(e) => setFilters((f) => ({ ...f, tipo: e.target.value || null, pagina: 1 }))}
        >
          {TIPO_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>

        <div className="flex items-center gap-2">
          <label className="text-gray-500">De:</label>
          <input
            type="date"
            className="rounded border px-2 py-1 text-sm"
            value={filters.data_inicio ?? ""}
            onChange={(e) => setFilters((f) => ({ ...f, data_inicio: e.target.value || null, pagina: 1 }))}
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-gray-500">Até:</label>
          <input
            type="date"
            className="rounded border px-2 py-1 text-sm"
            value={filters.data_fim ?? ""}
            onChange={(e) => setFilters((f) => ({ ...f, data_fim: e.target.value || null, pagina: 1 }))}
          />
        </div>
      </div>

      {/* Tabela */}
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />)}
        </div>
      ) : !result || result.itens.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum movimento encontrado.</p>
      ) : (
        <>
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="py-2 pr-4">Data</th>
                <th className="py-2 pr-4">Item</th>
                <th className="py-2 pr-4">Tipo</th>
                <th className="py-2 pr-4">Quantidade</th>
                <th className="py-2">Saldo após</th>
              </tr>
            </thead>
            <tbody>
              {result.itens.map((mov) => (
                <tr key={mov.id} className="border-b last:border-0">
                  <td className="py-2 pr-4 text-gray-500">
                    {new Date(mov.created_at).toLocaleString("pt-BR", {
                      day: "2-digit", month: "2-digit", year: "2-digit", hour: "2-digit", minute: "2-digit",
                    })}
                  </td>
                  <td className="py-2 pr-4 font-medium">{mov.item_nome}</td>
                  <td className="py-2 pr-4">
                    <span className={`rounded-full px-2 py-0.5 text-xs ${TIPO_BADGE[mov.tipo] ?? ""}`}>
                      {TIPO_LABEL[mov.tipo] ?? mov.tipo}
                    </span>
                  </td>
                  <td className={`py-2 pr-4 ${mov.tipo === "entrada" ? "text-green-700" : "text-red-600"}`}>
                    {mov.tipo === "entrada" ? "+" : "-"}{Number(mov.quantidade).toLocaleString("pt-BR")}
                  </td>
                  <td className="py-2 text-gray-600">
                    {Number(mov.saldo_apos).toLocaleString("pt-BR")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Paginação */}
          <div className="mt-4 flex items-center justify-between text-sm">
            <Button
              size="sm"
              variant="outline"
              disabled={(filters.pagina ?? 1) <= 1}
              onClick={() => setPage((filters.pagina ?? 1) - 1)}
            >
              ← Anterior
            </Button>
            <span className="text-gray-500">
              Página {filters.pagina ?? 1} de {totalPaginas} · {result.total} movimentos
            </span>
            <div className="flex items-center gap-2">
              <select
                className="rounded border px-2 py-1 text-sm"
                value={filters.por_pagina ?? 50}
                onChange={(e) => setFilters((f) => ({ ...f, por_pagina: Number(e.target.value), pagina: 1 }))}
              >
                {[25, 50, 100].map((n) => (
                  <option key={n} value={n}>{n} por página</option>
                ))}
              </select>
              <Button
                size="sm"
                variant="outline"
                disabled={(filters.pagina ?? 1) >= totalPaginas}
                onClick={() => setPage((filters.pagina ?? 1) + 1)}
              >
                Próximo →
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
