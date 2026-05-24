import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { formatCurrency } from "@/lib/format";
import { usePicoVendasHorario } from "./useRelatorios";

function diasAtras(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().split("T")[0];
}

function hoje(): string {
  return new Date().toISOString().split("T")[0];
}

function formatHora(h: number): string {
  return `${String(h).padStart(2, "0")}:00`;
}

export function PicoVendasHorarioPage() {
  const navigate = useNavigate();
  const [dataInicio, setDataInicio] = useState(() => diasAtras(30));
  const [dataFim, setDataFim] = useState(hoje);

  const { data, isLoading } = usePicoVendasHorario({ data_inicio: dataInicio, data_fim: dataFim });

  const maxComandas = data ? Math.max(...data.horarios.map((h) => h.total_comandas), 1) : 1;
  const horariosAtivos = data ? data.horarios.filter((h) => h.total_comandas > 0) : [];

  return (
    <div className="p-6">
      <button
        onClick={() => navigate("/relatorios")}
        className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800"
      >
        ← Relatórios
      </button>
      <h1 className="mb-6 text-xl font-semibold">Pico de Vendas por Horário</h1>

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

      {data && horariosAtivos.length > 0 && (
        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-lg border bg-white p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Horário de pico</p>
            <p className="mt-1 text-2xl font-semibold">
              {data.hora_pico !== null ? formatHora(data.hora_pico) : "—"}
            </p>
          </div>
          <div className="rounded-lg border bg-white p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Total de comandas</p>
            <p className="mt-1 text-2xl font-semibold">{data.total_comandas_periodo}</p>
          </div>
          <div className="rounded-lg border bg-white p-4">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Receita total</p>
            <p className="mt-1 text-2xl font-semibold">{formatCurrency(data.receita_total_periodo)}</p>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="h-8 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : !data ? null : horariosAtivos.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhuma venda registrada no período.</p>
      ) : (
        <div className="space-y-1">
          <div className="mb-2 grid grid-cols-[4rem_1fr_5rem_7rem] gap-2 text-xs font-semibold uppercase text-gray-500">
            <span>Hora</span>
            <span>Volume</span>
            <span className="text-right">Comandas</span>
            <span className="text-right">Receita</span>
          </div>
          {data.horarios
            .filter((h) => h.total_comandas > 0)
            .map((h) => {
              const isPico = h.hora === data.hora_pico;
              const pct = (h.total_comandas / maxComandas) * 100;
              return (
                <div
                  key={h.hora}
                  className={`grid grid-cols-[4rem_1fr_5rem_7rem] items-center gap-2 rounded px-2 py-1.5 text-sm ${isPico ? "bg-green-50 font-semibold" : "hover:bg-gray-50"}`}
                >
                  <span className={`font-mono ${isPico ? "text-green-700" : "text-gray-600"}`}>
                    {formatHora(h.hora)}
                  </span>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-4 rounded-full bg-gray-100 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${isPico ? "bg-green-500" : "bg-blue-400"}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                  <span className="text-right tabular-nums">{h.total_comandas}</span>
                  <span className="text-right tabular-nums">{formatCurrency(h.receita_total)}</span>
                </div>
              );
            })}
        </div>
      )}
    </div>
  );
}
