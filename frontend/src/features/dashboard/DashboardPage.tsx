import { useNavigate } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatCurrency } from "@/lib/format";
import { useDashboard } from "./useDashboard";

function CardSkeleton() {
  return <div className="animate-pulse h-24 rounded-lg bg-gray-100" />;
}

function ChartSkeleton() {
  return <div className="animate-pulse h-48 rounded-lg bg-gray-100" />;
}

function formatMinutos(min: number): string {
  if (min < 60) return `${min}min`;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return m > 0 ? `${h}h${m}min` : `${h}h`;
}

function HeatmapMes({ dados }: { dados: { data: string; faturamento: number }[] }) {
  if (dados.length === 0) return null;
  const max = Math.max(...dados.map((d) => d.faturamento), 1);

  const primeiro = new Date(dados[0].data + "T12:00:00");
  const offsetInicio = primeiro.getDay();

  function intensidade(val: number): string {
    const ratio = val / max;
    if (ratio === 0) return "bg-gray-100";
    if (ratio < 0.25) return "bg-green-100";
    if (ratio < 0.5) return "bg-green-300";
    if (ratio < 0.75) return "bg-green-500";
    return "bg-green-700";
  }

  const cells = [];
  for (let i = 0; i < offsetInicio; i++) {
    cells.push(<div key={`empty-${i}`} />);
  }
  for (const d of dados) {
    const dia = new Date(d.data + "T12:00:00").getDate();
    cells.push(
      <div
        key={d.data}
        title={`${dia}: ${formatCurrency(d.faturamento)}`}
        className={`flex items-center justify-center rounded text-xs font-medium ${intensidade(d.faturamento)} ${d.faturamento > 0 ? "text-white" : "text-gray-400"}`}
      >
        {dia}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-7 gap-1">
      {["D", "S", "T", "Q", "Q", "S", "S"].map((l, i) => (
        <div key={i} className="text-center text-xs text-gray-400 font-medium">
          {l}
        </div>
      ))}
      {cells}
    </div>
  );
}

export function DashboardPage() {
  const { data, isLoading } = useDashboard();
  const navigate = useNavigate();

  return (
    <main className="p-4 space-y-6">
      <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>

      {/* Cards */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {isLoading ? (
          <>
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </>
        ) : (
          <>
            <div className="rounded-lg border bg-white p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Faturamento Hoje</p>
              <p className="mt-1 text-2xl font-bold text-gray-900">
                {formatCurrency(data?.faturamento_hoje ?? 0)}
              </p>
            </div>
            <div className="rounded-lg border bg-white p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Ticket Médio</p>
              <p className="mt-1 text-2xl font-bold text-gray-900">
                {formatCurrency(data?.ticket_medio_hoje ?? 0)}
              </p>
            </div>
            <div className="rounded-lg border bg-white p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Comandas</p>
              <p className="mt-1 text-2xl font-bold text-gray-900">
                <span className="text-amber-600">{data?.comandas_abertas ?? 0}</span>
                <span className="text-sm font-normal text-gray-500"> abertas</span>
              </p>
              <p className="text-sm text-gray-500">{data?.comandas_fechadas_hoje ?? 0} fechadas hoje</p>
            </div>
            <div className="rounded-lg border bg-white p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Lucro Estimado</p>
              <p
                className={`mt-1 text-2xl font-bold ${
                  (data?.lucro_estimado_hoje ?? 0) >= 0 ? "text-green-600" : "text-red-600"
                }`}
              >
                {formatCurrency(data?.lucro_estimado_hoje ?? 0)}
              </p>
            </div>
          </>
        )}
      </div>

      {/* Gráficos — linha 1 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-lg border bg-white p-4">
          <h2 className="mb-3 text-sm font-medium text-gray-700">Faturamento por Hora (Hoje)</h2>
          {isLoading ? (
            <ChartSkeleton />
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={data?.faturamento_por_hora ?? []} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="hora" tick={{ fontSize: 11 }} interval={3} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `R$${v}`} />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} labelFormatter={(l) => `${l}h`} />
                <Bar dataKey="faturamento" fill="#3b82f6" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="rounded-lg border bg-white p-4">
          <h2 className="mb-3 text-sm font-medium text-gray-700">Top 10 Produtos (30 dias)</h2>
          {isLoading ? (
            <ChartSkeleton />
          ) : data?.top_10_produtos?.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-12">Sem vendas nos últimos 30 dias.</p>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart
                layout="vertical"
                data={data?.top_10_produtos ?? []}
                margin={{ top: 0, right: 20, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis
                  type="category"
                  dataKey="nome"
                  width={90}
                  tick={{ fontSize: 10 }}
                  tickFormatter={(v: string) => (v.length > 12 ? v.slice(0, 12) + "…" : v)}
                />
                <Tooltip formatter={(v) => [`${v} un`, "Quantidade"]} />
                <Bar dataKey="quantidade" fill="#10b981" radius={[0, 2, 2, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Gráficos — linha 2 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-lg border bg-white p-4">
          <h2 className="mb-3 text-sm font-medium text-gray-700">Últimos 30 Dias</h2>
          {isLoading ? (
            <ChartSkeleton />
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <LineChart
                data={data?.ultimos_30_dias ?? []}
                margin={{ top: 0, right: 0, left: -20, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis
                  dataKey="data"
                  tick={{ fontSize: 10 }}
                  interval={6}
                  tickFormatter={(v: string) => {
                    const d = new Date(v + "T12:00:00");
                    return `${d.getDate()}/${d.getMonth() + 1}`;
                  }}
                />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `R$${v}`} />
                <Tooltip
                  formatter={(v) => formatCurrency(Number(v))}
                  labelFormatter={(l) => {
                    const d = new Date(String(l) + "T12:00:00");
                    return `${d.getDate()}/${d.getMonth() + 1}/${d.getFullYear()}`;
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="faturamento"
                  stroke="#6366f1"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="rounded-lg border bg-white p-4">
          <h2 className="mb-3 text-sm font-medium text-gray-700">Calendário do Mês</h2>
          {isLoading ? (
            <ChartSkeleton />
          ) : (
            <HeatmapMes dados={data?.heatmap_mes ?? []} />
          )}
          <div className="mt-3 flex gap-2 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <span className="inline-block h-3 w-3 rounded bg-gray-100 border" /> R$0
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-3 w-3 rounded bg-green-100" /> baixo
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-3 w-3 rounded bg-green-500" /> médio
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-3 w-3 rounded bg-green-700" /> alto
            </span>
          </div>
        </div>
      </div>

      {/* Comandas Abertas */}
      <div className="rounded-lg border bg-white">
        <div className="px-4 py-3 border-b">
          <h2 className="text-sm font-medium text-gray-700">Comandas Abertas</h2>
        </div>
        {isLoading ? (
          <div className="p-4 space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse h-10 rounded bg-gray-100" />
            ))}
          </div>
        ) : !data?.comandas_abertas_lista?.length ? (
          <p className="p-6 text-center text-sm text-gray-400">Nenhuma comanda aberta.</p>
        ) : (
          <div className="divide-y">
            {data.comandas_abertas_lista.map((comanda) => (
              <div
                key={comanda.id}
                className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 cursor-pointer"
                onClick={() => navigate(`/comandas/${comanda.id}`)}
              >
                <div>
                  <span className="font-medium text-sm text-gray-900">{comanda.identificacao}</span>
                  <span className="ml-2 text-xs text-gray-500">
                    {comanda.qtd_itens} {comanda.qtd_itens === 1 ? "item" : "itens"}
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm font-medium text-gray-900">
                    {formatCurrency(comanda.total)}
                  </span>
                  <span className="text-xs text-gray-400">há {formatMinutos(comanda.aberta_ha_minutos)}</span>
                  <button
                    className="text-xs text-blue-600 hover:underline"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/comandas/${comanda.id}`);
                    }}
                  >
                    Abrir
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
