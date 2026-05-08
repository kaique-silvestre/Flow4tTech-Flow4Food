import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { formatCurrency } from "@/lib/format";
import { useComandasFechadas } from "@/features/comandas/useComandas";

function thirtyDaysAgo(): string {
  const d = new Date();
  d.setDate(d.getDate() - 30);
  return d.toISOString().slice(0, 10);
}

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

const fmtData = (iso: string | null | undefined) => {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export function HistoricoPage() {
  const navigate = useNavigate();
  const [busca, setBusca] = useState("");
  const [dataInicio, setDataInicio] = useState(thirtyDaysAgo);
  const [dataFim, setDataFim] = useState(todayISO);

  const { data: fechadas = [], isLoading } = useComandasFechadas({
    busca: busca || undefined,
    data_inicio: dataInicio,
    data_fim: dataFim,
  });

  return (
    <div className="p-6">
      <h1 className="mb-4 text-xl font-semibold">Histórico de Comandas</h1>

      <div className="mb-4 flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500">Data início</label>
          <input
            type="date"
            value={dataInicio}
            onChange={(e) => setDataInicio(e.target.value)}
            className="rounded border px-2 py-1.5 text-sm"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500">Data fim</label>
          <input
            type="date"
            value={dataFim}
            onChange={(e) => setDataFim(e.target.value)}
            className="rounded border px-2 py-1.5 text-sm"
          />
        </div>
        <Input
          placeholder="Buscar por nome ou mesa..."
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          className="max-w-xs"
        />
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : fechadas.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhuma comanda fechada no período.</p>
      ) : (
        <div className="space-y-2">
          {fechadas.map((c) => (
            <button
              key={c.id}
              onClick={() => navigate(`/comandas/${c.id}`)}
              className="w-full rounded border border-gray-200 p-3 text-left transition-colors hover:bg-gray-50"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-medium text-gray-700">
                    #{c.id} — {c.tipo_identificacao === "mesa" ? "Mesa" : ""} {c.identificacao}
                  </div>
                  <div className="text-xs text-gray-500">
                    Garçom: {c.garcom_nome} · Fechada em: {fmtData(c.data_fechamento)}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-gray-700">
                    {c.total != null ? formatCurrency(Number(c.total)) : "—"}
                  </div>
                  <div className="text-xs text-gray-400">total</div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
