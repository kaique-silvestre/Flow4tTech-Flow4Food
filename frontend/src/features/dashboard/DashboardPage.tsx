import { useNavigate } from "react-router-dom";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  Clock,
  Package,
  TrendingUp,
  Truck,
  Wallet,
} from "lucide-react";
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

function urgencyClass(minutos: number): string {
  if (minutos >= 120) return "border-l-4 border-l-red-400 bg-red-50/30";
  if (minutos >= 60) return "border-l-4 border-l-amber-400 bg-amber-50/30";
  return "";
}

function variacao(atual: number, anterior: number): number | null {
  if (anterior === 0) return null;
  return ((atual - anterior) / anterior) * 100;
}

function VariacaoBadge({ pct, label }: { pct: number | null; label: string }) {
  if (pct === null) return <span className="text-xs text-gray-400">{label}: —</span>;
  const up = pct >= 0;
  return (
    <span className={`inline-flex items-center gap-0.5 text-xs font-medium ${up ? "text-green-600" : "text-red-500"}`}>
      {up ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
      {Math.abs(pct).toFixed(1)}% {label}
    </span>
  );
}

export function DashboardPage() {
  const { data, isLoading } = useDashboard();
  const navigate = useNavigate();

  const cmvPct = data?.faturamento_hoje
    ? (data.cmv_hoje / data.faturamento_hoje) * 100
    : 0;

  const cmvColor =
    cmvPct === 0
      ? "text-gray-400"
      : cmvPct < 30
      ? "text-green-600"
      : cmvPct < 40
      ? "text-amber-600"
      : "text-red-600";

  const hasAlerts =
    (data?.contas_vencendo_7_dias_qtd ?? 0) > 0 ||
    (data?.entregas_esperadas_7_dias?.length ?? 0) > 0 ||
    (data?.insumos_criticos?.length ?? 0) > 0;

  const pctOntem = variacao(data?.faturamento_hoje ?? 0, data?.faturamento_ontem ?? 0);
  const pct7d = variacao(data?.faturamento_7d ?? 0, data?.faturamento_7d_anterior ?? 0);
  const pctMes = variacao(data?.faturamento_mes_atual ?? 0, data?.faturamento_mes_anterior ?? 0);

  return (
    <main className="p-4 space-y-4">
      <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>

      {/* Alertas */}
      {!isLoading && hasAlerts && (
        <div className="space-y-2">
          {(data?.contas_vencendo_7_dias_qtd ?? 0) > 0 && (
            <div className="flex items-start gap-3 rounded-lg border border-orange-200 bg-orange-50 px-4 py-3">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-orange-500" />
              <div>
                <p className="text-sm font-medium text-orange-800">
                  {data!.contas_vencendo_7_dias_qtd} conta{data!.contas_vencendo_7_dias_qtd > 1 ? "s" : ""} vencendo nos próximos 7 dias
                </p>
                <p className="text-xs text-orange-600">{formatCurrency(data!.contas_vencendo_7_dias_total)} em aberto</p>
              </div>
            </div>
          )}

          {(data?.entregas_esperadas_7_dias?.length ?? 0) > 0 && (
            <div className="flex items-start gap-3 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3">
              <Truck className="mt-0.5 h-4 w-4 shrink-0 text-blue-500" />
              <div>
                <p className="text-sm font-medium text-blue-800">
                  {data!.entregas_esperadas_7_dias.length} entrega{data!.entregas_esperadas_7_dias.length > 1 ? "s" : ""} esperada{data!.entregas_esperadas_7_dias.length > 1 ? "s" : ""} nos próximos 7 dias
                </p>
                <p className="text-xs text-blue-600">
                  {data!.entregas_esperadas_7_dias.slice(0, 2).map((e) =>
                    `${new Date(e.data_prevista_recebimento + "T00:00:00").toLocaleDateString("pt-BR")} · ${e.fornecedor_nome}`
                  ).join(" — ")}
                  {data!.entregas_esperadas_7_dias.length > 2 && ` e mais ${data!.entregas_esperadas_7_dias.length - 2}`}
                </p>
              </div>
            </div>
          )}

          {(data?.insumos_criticos?.length ?? 0) > 0 && (
            <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3">
              <Package className="mt-0.5 h-4 w-4 shrink-0 text-red-500" />
              <div>
                <p className="text-sm font-medium text-red-800">
                  {data!.insumos_criticos.length} insumo{data!.insumos_criticos.length > 1 ? "s" : ""} abaixo do nível crítico
                </p>
                <p className="text-xs text-red-600">
                  {data!.insumos_criticos.slice(0, 3).map((i) => i.nome).join(", ")}
                  {data!.insumos_criticos.length > 3 && ` e mais ${data!.insumos_criticos.length - 3}`}
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        {isLoading ? (
          <>
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </>
        ) : (
          <>
            <div className="rounded-lg border bg-white p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-4 w-4 text-gray-400" />
                <p className="text-xs text-gray-500 uppercase tracking-wide">Faturamento Hoje</p>
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(data?.faturamento_hoje ?? 0)}
              </p>
              <div className="mt-1 flex flex-col gap-0.5">
                <VariacaoBadge pct={pctOntem} label="vs ontem" />
              </div>
            </div>

            <div className="rounded-lg border bg-white p-4">
              <div className="flex items-center gap-2 mb-2">
                <Wallet className="h-4 w-4 text-gray-400" />
                <p className="text-xs text-gray-500 uppercase tracking-wide">Lucro Estimado</p>
              </div>
              <p className={`text-2xl font-bold ${(data?.lucro_estimado_hoje ?? 0) >= 0 ? "text-green-600" : "text-red-600"}`}>
                {formatCurrency(data?.lucro_estimado_hoje ?? 0)}
              </p>
              <p className="mt-1 text-xs text-gray-400">faturamento − CMV</p>
            </div>

            <div className="rounded-lg border bg-white p-4">
              <div className="flex items-center gap-2 mb-2">
                <Package className="h-4 w-4 text-gray-400" />
                <p className="text-xs text-gray-500 uppercase tracking-wide">CMV Hoje</p>
              </div>
              <p className={`text-2xl font-bold ${cmvColor}`}>
                {cmvPct.toFixed(1)}%
              </p>
              <p className="mt-1 text-xs text-gray-400">{formatCurrency(data?.cmv_hoje ?? 0)}</p>
            </div>

            <div className="rounded-lg border bg-white p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-4 w-4 text-gray-400" />
                <p className="text-xs text-gray-500 uppercase tracking-wide">Ticket Médio</p>
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(data?.ticket_medio_hoje ?? 0)}
              </p>
            </div>

            <div className="rounded-lg border bg-white p-4">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="h-4 w-4 text-gray-400" />
                <p className="text-xs text-gray-500 uppercase tracking-wide">Comandas</p>
              </div>
              <p className="text-2xl font-bold text-gray-900">
                <span className="text-amber-600">{data?.comandas_abertas ?? 0}</span>
                <span className="text-sm font-normal text-gray-500"> abertas</span>
              </p>
              <p className="mt-1 text-xs text-gray-400">{data?.comandas_fechadas_hoje ?? 0} fechadas hoje</p>
            </div>
          </>
        )}
      </div>

      {/* Cards de comparação */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {isLoading ? (
          <>
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </>
        ) : (
          <>
            <div className="rounded-lg border bg-white p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Ontem</p>
              <p className="text-xl font-semibold text-gray-800">{formatCurrency(data?.faturamento_ontem ?? 0)}</p>
              <VariacaoBadge pct={pctOntem} label="vs hoje" />
            </div>
            <div className="rounded-lg border bg-white p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Esta semana</p>
              <p className="text-xl font-semibold text-gray-800">{formatCurrency(data?.faturamento_7d ?? 0)}</p>
              <VariacaoBadge pct={pct7d} label="vs semana passada" />
            </div>
            <div className="rounded-lg border bg-white p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Este mês</p>
              <p className="text-xl font-semibold text-gray-800">{formatCurrency(data?.faturamento_mes_atual ?? 0)}</p>
              <VariacaoBadge pct={pctMes} label="vs mês passado" />
            </div>
          </>
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
                className={`flex items-center justify-between px-4 py-3 hover:bg-gray-50 cursor-pointer transition-colors ${urgencyClass(comanda.aberta_ha_minutos)}`}
                onClick={() => navigate(`/vendas/comandas/${comanda.id}`)}
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
                  <span className={`text-xs ${comanda.aberta_ha_minutos >= 120 ? "text-red-500 font-medium" : comanda.aberta_ha_minutos >= 60 ? "text-amber-500 font-medium" : "text-gray-400"}`}>
                    há {formatMinutos(comanda.aberta_ha_minutos)}
                  </span>
                  <button
                    className="text-xs text-blue-600 hover:underline"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/vendas/comandas/${comanda.id}`);
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

      {/* Gráfico 30 dias */}
      <div className="rounded-lg border bg-white p-4">
        <h2 className="mb-3 text-sm font-medium text-gray-700">Faturamento — Últimos 30 Dias</h2>
        {isLoading ? (
          <ChartSkeleton />
        ) : (
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart
              data={data?.ultimos_30_dias ?? []}
              margin={{ top: 4, right: 0, left: -20, bottom: 0 }}
            >
              <defs>
                <linearGradient id="gradFat" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
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
              <Area
                type="monotone"
                dataKey="faturamento"
                stroke="#6366f1"
                strokeWidth={2}
                fill="url(#gradFat)"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Faturamento por hora */}
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

      {/* Top 10 Produtos */}
      <div className="rounded-lg border bg-white p-4">
        <h2 className="mb-3 text-sm font-medium text-gray-700">Top 10 Produtos (30 dias)</h2>
        {isLoading ? (
          <ChartSkeleton />
        ) : !data?.top_10_produtos?.length ? (
          <p className="text-sm text-gray-400 text-center py-12">Sem vendas nos últimos 30 dias.</p>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart
              layout="vertical"
              data={data.top_10_produtos}
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
    </main>
  );
}
