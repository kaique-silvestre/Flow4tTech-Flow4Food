import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useFornecedores } from "@/features/cadastros/fornecedores/useFornecedores";
import { formatCurrency } from "@/lib/format";
import { useCompras, type CompraFilters } from "./useCompras";

export function ComprasPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<CompraFilters>({});
  const { data: compras = [], isLoading } = useCompras(filters);
  const { data: fornecedores = [] } = useFornecedores();

  const total = compras.reduce((sum, c) => sum + Number(c.total), 0);

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Compras</h1>
        <Button onClick={() => navigate("/compras/nova")}>+ Nova Compra</Button>
      </div>

      {/* Filtros */}
      <div className="mb-4 flex flex-wrap gap-3 text-sm">
        <div className="flex items-center gap-2">
          <label className="text-gray-500">De:</label>
          <input
            type="date"
            className="rounded border px-2 py-1 text-sm"
            value={filters.data_inicio ?? ""}
            onChange={(e) => setFilters((f) => ({ ...f, data_inicio: e.target.value || null }))}
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-gray-500">Até:</label>
          <input
            type="date"
            className="rounded border px-2 py-1 text-sm"
            value={filters.data_fim ?? ""}
            onChange={(e) => setFilters((f) => ({ ...f, data_fim: e.target.value || null }))}
          />
        </div>
        <select
          className="rounded border px-2 py-1 text-sm"
          value={filters.fornecedor_id ?? ""}
          onChange={(e) =>
            setFilters((f) => ({ ...f, fornecedor_id: e.target.value ? Number(e.target.value) : null }))
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
      ) : compras.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhuma compra encontrada.</p>
      ) : (
        <div className="space-y-2">
          {compras.map((compra) => (
            <div key={compra.id} className="flex items-center justify-between rounded border p-3">
              <div>
                <div className="font-medium">
                  {new Date(compra.data_compra + "T00:00:00").toLocaleDateString("pt-BR")}
                  {" · "}
                  <span className="text-gray-600">{compra.fornecedor_nome ?? "Sem fornecedor"}</span>
                </div>
                <div className="text-xs text-gray-400">
                  Nota: {compra.numero_nota ?? "—"} · {compra.itens.length} {compra.itens.length === 1 ? "item" : "itens"}
                </div>
              </div>
              <div className="text-right">
                <div className="font-semibold">{formatCurrency(compra.total)}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {compras.length > 0 && (
        <div className="mt-4 text-right text-sm text-gray-500">
          Total no período: <span className="font-semibold text-gray-800">{formatCurrency(total)}</span>
        </div>
      )}
    </div>
  );
}
