import { useState } from "react";
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
import {
  useDashboard,
  useDashboardHistorico,
  useDashboardResumoAnual,
} from "./useDashboard";

const MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

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

function hoje(): string {
  return new Date().toISOString().split("T")[0];
}

function diasAtras(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().split("T")[0];
}

function TabHistorico() {
  const anoAtual = new Date().getFullYear();
  const [inicio, setInicio] = useState(diasAtras(29));
  const [fim, setFim] = useState(hoje());
  const [ano, setAno] = useState(anoAtual);

  const { data: historico = [], isLoading: loadingHistorico } = useDashboardHistorico(inicio, fim);
  const { data: resumoAnual = [], isLoading: loadingAnual } = useDashboardResumoAnual(ano);

  return (
    <div className="space-y-6">
      {/* Date picker */}
      <div className="rounded-lg border bg-white p-4">
        <div className="flex flex-wrap items-end gap-4 mb-4">
          <div className="space-y-1">
            <label className="text-xs text-gray-500">De</label>
            <input
              type="date"
              value={inicio}
              onChange={(e) => setInicio(e.target.value)}
              className="rounded border px-2 py-1.5 text-sm"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-gray-500">Até</label>
            <input
              type="date"
              value={fim}
              onChange={(e) => setFim(e.target.value)}
              className="rounded border px-2 py-1.5 text-sm"
            />
          </div>
        </div>

        {loadingHistorico ? (
          <div className="animate-pulse h-40 rounded bg-gray-100" />
        ) : historico.length === 0 ? (
          <p className="text-sm text-gray-400 py-6 text-center">Sem dados no período.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-xs text-gray-500">
                  <th className="text-left pb-2 font-medium">Data</th>
                  <th className="text-right pb-2 font-medium">Faturamento</th>
                  <th className="text-right pb-2 font-medium">Gastos (Compras)</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {historico
                  .filter((row) => row.faturamento > 0 || row.total_compras > 0)
                  .map((row) => {
                    const d = new Date(row.data + "T12:00:00");
                    const label = `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`;
                    return (
                      <tr key={row.data} className="hover:bg-gray-50">
                        <td className="py-2 text-gray-700">{label}</td>
                        <td className="py-2 text-right text-gray-900">
                          {row.faturamento > 0 ? formatCurrency(row.faturamento) : "—"}
                        </td>
                        <td className="py-2 text-right text-gray-900">
                          {row.total_compras > 0 ? formatCurrency(row.total_compras) : "—"}
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
              <tfoot className="border-t font-medium">
                <tr>
                  <td className="pt-2 text-gray-700">Total</td>
                  <td className="pt-2 text-right text-gray-900">
                    {formatCurrency(historico.reduce((s, r) => s + r.faturamento, 0))}
                  </td>
                  <td className="pt-2 text-right text-gray-900">
                    {formatCurrency(historico.reduce((s, r) => s + r.total_compras, 0))}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>

      {/* Calendário anual */}
      <div className="rounded-lg border bg-white p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-medium text-gray-700">Calendário Anual</h2>
          <div className="flex items-center gap-2">
            <button
              className="rounded border px-2 py-1 text-xs hover:bg-gray-50"
              onClick={() => setAno((a) => a - 1)}
            >
              ‹
            </button>
            <span className="text-sm font-medium">{ano}</span>
            <button
              className="rounded border px-2 py-1 text-xs hover:bg-gray-50"
              onClick={() => setAno((a) => a + 1)}
            >
              ›
            </button>
          </div>
        </div>

        {loadingAnual ? (
          <div className="animate-pulse h-20 rounded bg-gray-100" />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr>
                  <th className="text-left pr-3 py-1 font-medium text-gray-500 w-24">Métrica</th>
                  {MESES.map((m) => (
                    <th key={m} className="text-center py-1 font-medium text-gray-500 min-w-[52px]">{m}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="pr-3 py-2 font-medium text-gray-700">Faturamento</td>
                  {resumoAnual.map((item) => (
                    <td key={item.mes} className="text-center py-2 text-gray-900">
                      {item.faturamento > 0 ? formatCurrency(item.faturamento) : "—"}
                    </td>
                  ))}
                </tr>
                <tr className="border-t">
                  <td className="pr-3 py-2 font-medium text-gray-700">Gastos</td>
                  {resumoAnual.map((item) => (
                    <td key={item.mes} className="text-center py-2 text-gray-900">
                      {item.total_compras > 0 ? formatCurrency(item.total_compras) : "—"}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { data, isLoading } = useDashboard();
  const navigate = useNavigate();
  const [tab, setTab] = useState<"resumo" | "historico">("resumo");

  return (
    <main className="p-4 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
        <div className="flex gap-1 rounded-lg border bg-gray-50 p-1">
          <button
            onClick={() => setTab("resumo")}
            className={`rounded px-3 py-1 text-sm transition-colors ${
              tab === "resumo"
                ? "bg-white font-medium text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Resumo
          </button>
          <button
            onClick={() => setTab("historico")}
            className={`rounded px-3 py-1 text-sm transition-colors ${
              tab === "historico"
                ? "bg-white font-medium text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Histórico
          </button>
        </div>
      </div>

      {tab === "historico" ? (
        <TabHistorico />
      ) : (
        <>
          {/* Cards */}
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
            {isLoading ? (
              <>
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
        </>
      )}
    </main>
  );
}
