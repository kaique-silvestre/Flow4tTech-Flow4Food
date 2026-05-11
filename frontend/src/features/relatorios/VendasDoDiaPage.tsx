import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { formatCurrency, formatDate } from "@/lib/format";
import { useVendasDoDia } from "./useRelatorios";

export function VendasDoDiaPage() {
  const [data, setData] = useState(() => new Date().toISOString().slice(0, 10));
  const navigate = useNavigate();
  const { data: vendas, isLoading } = useVendasDoDia(data);

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center gap-4">
        <div>
          <h1 className="text-xl font-semibold">Vendas do Dia</h1>
          {vendas && (
            <p className="text-sm text-gray-500">
              {new Date(vendas.data + "T12:00:00").toLocaleDateString("pt-BR", {
                weekday: "long",
                day: "2-digit",
                month: "long",
                year: "numeric",
              })}
            </p>
          )}
        </div>
        <input
          type="date"
          value={data}
          onChange={(e) => setData(e.target.value)}
          className="rounded border px-2 py-1 text-sm"
        />
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : !vendas ? null : (
        <>
          {/* Resumo */}
          <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-5">
            <div className="rounded border p-3">
              <p className="text-xs text-gray-500">Comandas</p>
              <p className="text-lg font-semibold">{vendas.qtd_comandas}</p>
            </div>
            <div className="rounded border p-3">
              <p className="text-xs text-gray-500">Faturamento Bruto</p>
              <p className="text-lg font-semibold">{formatCurrency(vendas.faturamento_bruto)}</p>
            </div>
            <div className="rounded border p-3">
              <p className="text-xs text-gray-500">Descontos</p>
              <p className="text-lg font-semibold text-red-600">
                {formatCurrency(vendas.total_descontos)}
              </p>
            </div>
            <div className="rounded border p-3">
              <p className="text-xs text-gray-500">Cortesias</p>
              <p className="text-lg font-semibold text-orange-600">
                {formatCurrency(vendas.total_cortesias)}
              </p>
            </div>
            <div className="rounded border bg-green-50 p-3">
              <p className="text-xs text-gray-500">Faturamento Líquido</p>
              <p className="text-lg font-semibold text-green-700">
                {formatCurrency(vendas.faturamento_liquido)}
              </p>
            </div>
          </div>

          {/* Por método */}
          {vendas.por_metodo.length > 0 && (
            <div className="mb-6">
              <h2 className="mb-2 text-sm font-semibold uppercase text-gray-600">
                Por Método de Pagamento
              </h2>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500">
                    <th className="pb-1">Método</th>
                    <th className="pb-1 text-right">Total</th>
                    <th className="pb-1 text-right">Transações</th>
                  </tr>
                </thead>
                <tbody>
                  {vendas.por_metodo.map((m) => (
                    <tr key={m.metodo_id} className="border-b">
                      <td className="py-2">{m.metodo_nome}</td>
                      <td className="py-2 text-right">{formatCurrency(m.total)}</td>
                      <td className="py-2 text-right">{m.qtd}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Comandas */}
          <div>
            <h2 className="mb-2 text-sm font-semibold uppercase text-gray-600">Comandas</h2>
            {vendas.comandas.length === 0 ? (
              <p className="text-sm text-gray-500">Nenhuma comanda fechada neste dia.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500">
                    <th className="pb-1">ID</th>
                    <th className="pb-1">Identificação</th>
                    <th className="pb-1">Garçom</th>
                    <th className="pb-1 text-right">Total</th>
                    <th className="pb-1 text-right">Desconto</th>
                    <th className="pb-1 text-right">Fechamento</th>
                  </tr>
                </thead>
                <tbody>
                  {vendas.comandas.map((c) => (
                    <tr
                      key={c.id}
                      onClick={() => navigate(`/comandas/${c.id}`)}
                      className="border-b hover:bg-gray-50 cursor-pointer"
                    >
                      <td className="py-2 text-gray-400">#{c.id}</td>
                      <td className="py-2">{c.identificacao}</td>
                      <td className="py-2">{c.garcom_nome}</td>
                      <td className="py-2 text-right">{formatCurrency(c.total)}</td>
                      <td className="py-2 text-right">
                        {c.desconto_valor ? formatCurrency(c.desconto_valor) : "—"}
                      </td>
                      <td className="py-2 text-right">{formatDate(c.data_fechamento)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  );
}
