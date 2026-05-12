import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { formatCurrency } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { useFechamentoCaixa } from "./useRelatorios";

function toIsoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export function FechamentoCaixaPage() {
  const navigate = useNavigate();
  const [data, setData] = useState(toIsoDate(new Date()));
  const { data: relatorio, isLoading } = useFechamentoCaixa(data);

  return (
    <div className="p-6">
      <button
        onClick={() => navigate("/relatorios")}
        className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800 print:hidden"
      >
        ← Relatórios
      </button>
      {/* Controles — ocultos na impressão */}
      <div className="mb-6 flex items-center justify-between print:hidden">
        <h1 className="text-xl font-semibold">Fechamento de Caixa</h1>
        <div className="flex items-center gap-3">
          <input
            type="date"
            className="rounded border px-2 py-1 text-sm"
            value={data}
            onChange={(e) => setData(e.target.value)}
          />
          <Button onClick={() => window.print()} variant="outline" size="sm">
            Exportar PDF
          </Button>
        </div>
      </div>

      {/* Título de impressão — visível apenas no PDF */}
      <div className="mb-4 hidden print:block">
        <h1 className="text-xl font-bold">
          FECHAMENTO DE CAIXA —{" "}
          {data
            ? new Date(data + "T12:00:00").toLocaleDateString("pt-BR", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
              })
            : ""}
        </h1>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : !relatorio ? (
        <p className="text-sm text-gray-500">Selecione uma data.</p>
      ) : (
        <div className="max-w-lg rounded border p-6">
          <div className="mb-6 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Total de comandas fechadas:</span>
              <span className="font-semibold">{relatorio.qtd_comandas}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Faturamento bruto:</span>
              <span className="font-semibold">{formatCurrency(relatorio.faturamento_bruto)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Descontos aplicados:</span>
              <span className="font-semibold text-red-600">
                {formatCurrency(relatorio.descontos)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Cortesias:</span>
              <span className="font-semibold text-orange-600">
                {formatCurrency(relatorio.cortesias)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Comissões garçons (a pagar):</span>
              <span className="font-semibold text-blue-600">
                {formatCurrency(relatorio.total_comissoes)}
              </span>
            </div>
            <div className="flex justify-between border-t pt-2">
              <span className="font-semibold">Faturamento líquido:</span>
              <span className="font-bold text-green-700">
                {formatCurrency(relatorio.faturamento_liquido)}
              </span>
            </div>
          </div>

          {relatorio.por_metodo.length > 0 && (
            <div>
              <h2 className="mb-2 text-xs font-semibold uppercase text-gray-500">
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
                  {relatorio.por_metodo.map((m) => (
                    <tr key={m.metodo_id} className="border-b">
                      <td className="py-1">{m.metodo_nome}</td>
                      <td className="py-1 text-right">{formatCurrency(m.total)}</td>
                      <td className="py-1 text-right">{m.qtd}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
