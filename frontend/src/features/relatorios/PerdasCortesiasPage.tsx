import { useState } from "react";
import { formatCurrency } from "@/lib/format";
import { usePerdasCortesias } from "./useRelatorios";

const MOTIVO_LABEL: Record<string, string> = {
  consumo_interno: "Consumo Interno",
  perda: "Perda",
  quebra: "Quebra",
  cortesia: "Cortesia (Baixa)",
  outro: "Outro",
};

function diasAtras(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().split("T")[0];
}

function hoje(): string {
  return new Date().toISOString().split("T")[0];
}

export function PerdasCortesiasPage() {
  const [dataInicio, setDataInicio] = useState(() => diasAtras(30));
  const [dataFim, setDataFim] = useState(hoje);

  const { data, isLoading } = usePerdasCortesias({
    data_inicio: dataInicio,
    data_fim: dataFim,
  });

  return (
    <div className="p-6">
      <h1 className="mb-6 text-xl font-semibold">Perdas e Cortesias</h1>

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
      ) : !data ? null : data.grupos.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhuma perda registrada no período.</p>
      ) : (
        <>
          <div className="mb-4 inline-block rounded border bg-gray-50 px-4 py-2 text-sm">
            <span className="text-gray-500">Total geral: </span>
            <span className="font-semibold">{formatCurrency(data.total_geral)}</span>
          </div>

          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-xs font-semibold uppercase text-gray-500">
                <th className="pb-2">Motivo</th>
                <th className="pb-2 text-right">Movimentos</th>
                <th className="pb-2 text-right">Total (Custo)</th>
              </tr>
            </thead>
            <tbody>
              {data.grupos.map((g) => (
                <tr key={g.motivo} className="border-b">
                  <td className="py-2">{MOTIVO_LABEL[g.motivo] ?? g.motivo}</td>
                  <td className="py-2 text-right">{g.qtd_movimentos}</td>
                  <td className="py-2 text-right">{formatCurrency(g.total_valor)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
