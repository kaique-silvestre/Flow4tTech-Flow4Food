import { useState } from "react";
import { formatCurrency } from "@/lib/format";
import { useDRE } from "./useRelatorios";

function mesAtual(): string {
  const hoje = new Date();
  return `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, "0")}`;
}

export function DrePage() {
  const [mes, setMes] = useState(mesAtual);
  const { data, isLoading } = useDRE(mes);

  const positivo = data && data.lucro_bruto >= 0;

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center gap-4">
        <h1 className="text-xl font-semibold">DRE Simplificado</h1>
        <input
          type="month"
          value={mes}
          onChange={(e) => setMes(e.target.value)}
          className="rounded border px-2 py-1 text-sm"
        />
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-8 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : !data ? null : (
        <div className="max-w-lg space-y-6">
          {data.produtos_sem_custo.length > 0 && (
            <div className="rounded border border-yellow-300 bg-yellow-50 p-3 text-sm">
              <p className="font-semibold text-yellow-800">
                ⚠ {data.produtos_sem_custo.length} produto(s) sem custo cadastrado — CMV pode estar
                subestimado.
              </p>
              <ul className="mt-1 list-inside list-disc text-yellow-700">
                {data.produtos_sem_custo.map((p) => (
                  <li key={p.item_id}>{p.nome}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Receita */}
          <div>
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">
              Receita
            </h2>
            <div className="space-y-1 rounded border p-4 text-sm">
              <div className="flex justify-between">
                <span>Faturamento bruto</span>
                <span className="font-medium">{formatCurrency(data.faturamento_bruto)}</span>
              </div>
              <div className="flex justify-between text-red-600">
                <span>(-) Descontos</span>
                <span>{formatCurrency(data.descontos)}</span>
              </div>
              <div className="flex justify-between text-orange-600">
                <span>(-) Cortesias</span>
                <span>{formatCurrency(data.cortesias_valor)}</span>
              </div>
              <div className="flex justify-between border-t pt-1 font-semibold">
                <span>Faturamento líquido</span>
                <span>{formatCurrency(data.faturamento_liquido)}</span>
              </div>
            </div>
          </div>

          {/* Custos */}
          <div>
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">
              Custos
            </h2>
            <div className="space-y-1 rounded border p-4 text-sm">
              <div className="flex justify-between">
                <span>Custo das mercadorias (CMV)</span>
                <span className="font-medium">{formatCurrency(data.cmv)}</span>
              </div>
              <div className="flex justify-between">
                <span>Perdas / Quebras</span>
                <span>{formatCurrency(data.perdas)}</span>
              </div>
              <div className="flex justify-between">
                <span>Comissões garçons (10%)</span>
                <span className="text-blue-600">{formatCurrency(data.comissoes)}</span>
              </div>
              <div className="flex justify-between border-t pt-1 font-semibold">
                <span>Total de custos</span>
                <span>{formatCurrency(data.total_custos)}</span>
              </div>
            </div>
          </div>

          {/* Resultado */}
          <div
            className={`rounded border p-4 ${positivo ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"}`}
          >
            <div className="flex justify-between text-lg font-bold">
              <span>Lucro bruto</span>
              <span className={positivo ? "text-green-700" : "text-red-700"}>
                {formatCurrency(data.lucro_bruto)}
              </span>
            </div>
            <div className="mt-1 flex justify-between text-sm font-medium text-gray-600">
              <span>Margem</span>
              <span>{Number(data.margem_percentual).toFixed(1)}%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
