import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatCurrency, formatQuantidade, parseApiDate } from "@/lib/format";
import {
  useResumoConsumo,
  useItensConsumo,
  type PeriodParams,
  type ResumoConsumidorResponse,
  type ItemConsumoInternoResponse,
} from "./useConsumoInterno";
import { LancarConsumoModal } from "./LancarConsumoModal";
import { ConsumoCalendar } from "./ConsumoCalendar";

// ---------------------------------------------------------------------------
// Period helpers
// ---------------------------------------------------------------------------

type PeriodMode = "semana" | "mes" | "ano";
type ViewMode = "consumidor" | "lancamento";

const MESES = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

function toIsoDate(d: Date): string {
  return d.toISOString().split("T")[0];
}

function getWeekBounds(anchor: Date): { start: Date; end: Date } {
  const start = new Date(anchor);
  const day = start.getDay();
  start.setDate(start.getDate() + (day === 0 ? -6 : 1 - day));
  start.setHours(0, 0, 0, 0);
  const end = new Date(start);
  end.setDate(end.getDate() + 6);
  end.setHours(23, 59, 59, 999);
  return { start, end };
}

function toPeriodParams(anchor: Date, mode: PeriodMode): PeriodParams {
  if (mode === "mes") return { mes: anchor.getMonth() + 1, ano: anchor.getFullYear() };
  if (mode === "ano") {
    const ano = anchor.getFullYear();
    return { data_inicio: `${ano}-01-01`, data_fim: `${ano}-12-31` };
  }
  const { start, end } = getWeekBounds(anchor);
  return { data_inicio: toIsoDate(start), data_fim: toIsoDate(end) };
}

function periodLabel(anchor: Date, mode: PeriodMode): string {
  if (mode === "mes") return `${MESES[anchor.getMonth()]} ${anchor.getFullYear()}`;
  if (mode === "ano") return String(anchor.getFullYear());
  const { start, end } = getWeekBounds(anchor);
  const fmt = (d: Date) => d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
  return `${fmt(start)} – ${fmt(end)}/${end.getFullYear()}`;
}

function navigateAnchor(anchor: Date, mode: PeriodMode, delta: number): Date {
  const next = new Date(anchor);
  if (mode === "mes") next.setMonth(next.getMonth() + delta);
  else if (mode === "ano") next.setFullYear(next.getFullYear() + delta);
  else next.setDate(next.getDate() + delta * 7);
  return next;
}

function isCurrentPeriod(anchor: Date, mode: PeriodMode): boolean {
  const now = new Date();
  if (mode === "mes") return anchor.getMonth() === now.getMonth() && anchor.getFullYear() === now.getFullYear();
  if (mode === "ano") return anchor.getFullYear() === now.getFullYear();
  const { start, end } = getWeekBounds(now);
  return anchor >= start && anchor <= end;
}

// ---------------------------------------------------------------------------
// Re-aggregate resumo from flat items (used when a day is selected)
// ---------------------------------------------------------------------------

function computeResumoFromItems(items: ItemConsumoInternoResponse[]): ResumoConsumidorResponse[] {
  const map = new Map<number, { nome: string; total: number; count: number; last: string }>();
  for (const item of items) {
    const prev = map.get(item.consumidor_id);
    if (prev) {
      prev.total += Number(item.subtotal);
      prev.count += 1;
      if (item.created_at > prev.last) prev.last = item.created_at;
    } else {
      map.set(item.consumidor_id, {
        nome: item.consumidor_nome,
        total: Number(item.subtotal),
        count: 1,
        last: item.created_at,
      });
    }
  }
  return Array.from(map.entries()).map(([id, v]) => ({
    consumidor_id: id,
    consumidor_nome: v.nome,
    itens_no_mes: v.count,
    total: v.total,
    ultima_atividade: v.last,
  }));
}

// ---------------------------------------------------------------------------
// Date formatter
// ---------------------------------------------------------------------------

const fmtData = (iso: string | null | undefined) => {
  if (!iso) return "—";
  return parseApiDate(iso).toLocaleString("pt-BR", {
    day: "2-digit", month: "2-digit", year: "2-digit",
    hour: "2-digit", minute: "2-digit",
  });
};

const fmtDayLabel = (iso: string) => {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y.slice(2)}`;
};

function localDateKey(isoUtc: string): string {
  const d = parseApiDate(isoUtc);
  const y = d.getFullYear();
  const mo = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${mo}-${day}`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ConsumoInternoPage() {
  const navigate = useNavigate();
  const [anchor, setAnchor] = useState(new Date());
  const [periodMode, setPeriodMode] = useState<PeriodMode>("mes");
  const [viewMode, setViewMode] = useState<ViewMode>("consumidor");
  const [busca, setBusca] = useState("");
  const [selectedDay, setSelectedDay] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);

  const period = toPeriodParams(anchor, periodMode);

  const { data: resumo = [], isLoading: loadingResumo } = useResumoConsumo(period);
  // Always fetch items — needed for calendar day aggregation
  const { data: itens = [], isLoading: loadingItens } = useItensConsumo(period);

  // ── Derived data with day filter + search ──────────────────────────────────
  const effectiveItens = useMemo(() => {
    let r = itens;
    if (selectedDay) r = r.filter((i) => localDateKey(i.created_at) === selectedDay);
    if (busca.trim()) r = r.filter((i) => i.consumidor_nome.toLowerCase().includes(busca.toLowerCase()));
    return r;
  }, [itens, selectedDay, busca]);

  const effectiveResumo = useMemo(() => {
    const base = selectedDay ? computeResumoFromItems(itens.filter((i) => localDateKey(i.created_at) === selectedDay)) : resumo;
    return busca.trim() ? base.filter((r) => r.consumidor_nome.toLowerCase().includes(busca.toLowerCase())) : base;
  }, [itens, resumo, selectedDay, busca]);

  // ── KPIs (always from full period, no day/busca filter) ────────────────────
  const totalGeral = resumo.reduce((acc, r) => acc + Number(r.total), 0);
  const totalLancamentos = resumo.reduce((acc, r) => acc + r.itens_no_mes, 0);
  const topConsumidor = resumo.length ? resumo.reduce((max, r) => Number(r.total) > Number(max.total) ? r : max) : null;

  // ── Navigation ──────────────────────────────────────────────────────────────
  function changeAnchor(delta: number) {
    setAnchor((a) => navigateAnchor(a, periodMode, delta));
    setSelectedDay(null);
  }

  function changeMode(m: PeriodMode) {
    setPeriodMode(m);
    setAnchor(new Date());
    setSelectedDay(null);
  }

  function goToday() {
    setAnchor(new Date());
    setSelectedDay(null);
  }

  function handleMonthNavigate(year: number, month: number) {
    setPeriodMode("mes");
    setAnchor(new Date(year, month - 1, 1));
    setSelectedDay(null);
  }

  const isLoading = loadingResumo || loadingItens;

  return (
    <div className="p-4 lg:p-6">
      {/* Header */}
      <div className="mb-5 flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl font-semibold">Consumo Interno</h1>
        <Button onClick={() => setShowModal(true)}>+ Lançar Consumo</Button>
      </div>

      {/* Period mode tabs + navigator */}
      <div className="mb-5 flex flex-wrap items-center gap-3">
        <div className="flex overflow-hidden rounded border text-sm">
          {(["semana", "mes", "ano"] as PeriodMode[]).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => changeMode(m)}
              className={`px-3 py-1.5 transition-colors ${
                periodMode === m ? "bg-gray-900 text-white" : "bg-white text-gray-600 hover:bg-gray-50"
              }`}
            >
              {m === "mes" ? "Mês" : m.charAt(0).toUpperCase() + m.slice(1)}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => changeAnchor(-1)}
            className="flex h-8 w-8 items-center justify-center rounded border text-gray-600 hover:bg-gray-50"
          >
            ◀
          </button>
          <span className="min-w-[180px] text-center text-sm font-medium">
            {periodLabel(anchor, periodMode)}
          </span>
          <button
            type="button"
            onClick={() => changeAnchor(1)}
            className="flex h-8 w-8 items-center justify-center rounded border text-gray-600 hover:bg-gray-50"
          >
            ▶
          </button>
        </div>

        {!isCurrentPeriod(anchor, periodMode) && (
          <button
            type="button"
            onClick={goToday}
            className="rounded border px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
          >
            Hoje
          </button>
        )}
      </div>

      {/* KPI cards */}
      <div className="mb-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded border bg-white p-4">
          <p className="text-xs text-gray-500">Total gasto</p>
          <p className="mt-1 text-2xl font-bold">{formatCurrency(totalGeral)}</p>
        </div>
        <div className="rounded border bg-white p-4">
          <p className="text-xs text-gray-500">Lançamentos</p>
          <p className="mt-1 text-2xl font-bold">{totalLancamentos}</p>
          <p className="mt-0.5 text-xs text-gray-400">
            {resumo.length} {resumo.length === 1 ? "consumidor" : "consumidores"}
          </p>
        </div>
        <div className="rounded border bg-white p-4">
          <p className="text-xs text-gray-500">Maior consumo</p>
          {topConsumidor ? (
            <>
              <p className="mt-1 truncate text-base font-semibold">{topConsumidor.consumidor_nome}</p>
              <p className="mt-0.5 text-xs text-gray-400">{formatCurrency(Number(topConsumidor.total))}</p>
            </>
          ) : (
            <p className="mt-1 text-sm text-gray-400">—</p>
          )}
        </div>
      </div>

      {/* Calendar */}
      {isLoading ? (
        <div className="mb-4 h-48 animate-pulse rounded border bg-gray-100" />
      ) : (
        <ConsumoCalendar
          items={itens}
          periodMode={periodMode}
          anchor={anchor}
          selectedDay={selectedDay}
          onDaySelect={setSelectedDay}
          onMonthNavigate={handleMonthNavigate}
        />
      )}

      {/* Controls: search + day badge + view toggle */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Input
          placeholder="Buscar consumidor..."
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          className="max-w-xs"
        />

        {selectedDay && (
          <div className="flex items-center gap-1.5 rounded border border-blue-200 bg-blue-50 px-2.5 py-1 text-sm text-blue-700">
            <span>{fmtDayLabel(selectedDay)}</span>
            <button type="button" onClick={() => setSelectedDay(null)} className="text-blue-400 hover:text-blue-600">
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        )}

        <div className="ml-auto flex overflow-hidden rounded border text-sm">
          <button
            type="button"
            onClick={() => setViewMode("consumidor")}
            className={`px-3 py-1.5 transition-colors ${
              viewMode === "consumidor" ? "bg-gray-900 text-white" : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            Por consumidor
          </button>
          <button
            type="button"
            onClick={() => setViewMode("lancamento")}
            className={`px-3 py-1.5 transition-colors ${
              viewMode === "lancamento" ? "bg-gray-900 text-white" : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            Por lançamento
          </button>
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-14 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : viewMode === "consumidor" ? (
        effectiveResumo.length === 0 ? (
          <p className="text-sm text-gray-500">
            {selectedDay ? `Nenhum consumo em ${fmtDayLabel(selectedDay)}.` : "Nenhum consumo registrado neste período."}
          </p>
        ) : (
          <>
            <div className="hidden overflow-x-auto sm:block">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500">
                    <th className="pb-2 font-medium">Consumidor</th>
                    <th className="pb-2 font-medium text-center">Itens</th>
                    <th className="pb-2 font-medium text-right">Total</th>
                    <th className="pb-2 font-medium text-right">Última atividade</th>
                  </tr>
                </thead>
                <tbody>
                  {effectiveResumo.map((r) => (
                    <tr
                      key={r.consumidor_id}
                      onClick={() => navigate(`/consumo-interno/${r.consumidor_id}?mes=${period.mes ?? ""}&ano=${period.ano ?? ""}`)}
                      className="cursor-pointer border-b transition-colors hover:bg-gray-50"
                    >
                      <td className="py-3 font-medium">{r.consumidor_nome}</td>
                      <td className="py-3 text-center">{r.itens_no_mes}</td>
                      <td className="py-3 text-right font-medium">{formatCurrency(Number(r.total))}</td>
                      <td className="py-3 text-right text-gray-500">{fmtData(r.ultima_atividade)}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t-2">
                    <td className="pt-3 font-semibold">Total</td>
                    <td className="pt-3 text-center font-semibold">
                      {effectiveResumo.reduce((a, r) => a + r.itens_no_mes, 0)}
                    </td>
                    <td className="pt-3 text-right font-semibold">
                      {formatCurrency(effectiveResumo.reduce((a, r) => a + Number(r.total), 0))}
                    </td>
                    <td />
                  </tr>
                </tfoot>
              </table>
            </div>

            <div className="space-y-2 sm:hidden">
              {effectiveResumo.map((r) => (
                <button
                  key={r.consumidor_id}
                  type="button"
                  onClick={() => navigate(`/consumo-interno/${r.consumidor_id}?mes=${period.mes ?? ""}&ano=${period.ano ?? ""}`)}
                  className="w-full rounded border p-4 text-left transition-colors hover:bg-gray-50"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{r.consumidor_nome}</span>
                    <span className="font-semibold">{formatCurrency(Number(r.total))}</span>
                  </div>
                  <div className="mt-1 text-xs text-gray-500">
                    {r.itens_no_mes} {r.itens_no_mes === 1 ? "item" : "itens"} · Último: {fmtData(r.ultima_atividade)}
                  </div>
                </button>
              ))}
              <div className="rounded bg-gray-50 p-3 text-right font-semibold">
                Total: {formatCurrency(effectiveResumo.reduce((a, r) => a + Number(r.total), 0))}
              </div>
            </div>
          </>
        )
      ) : effectiveItens.length === 0 ? (
        <p className="text-sm text-gray-500">
          {selectedDay ? `Nenhum lançamento em ${fmtDayLabel(selectedDay)}.` : "Nenhum lançamento neste período."}
        </p>
      ) : (
        <>
          <div className="hidden overflow-x-auto sm:block">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="pb-2 font-medium">Consumidor</th>
                  <th className="pb-2 font-medium">Item</th>
                  <th className="pb-2 font-medium text-center">Qtd</th>
                  <th className="pb-2 font-medium text-right">Custo unit.</th>
                  <th className="pb-2 font-medium text-right">Subtotal</th>
                  <th className="pb-2 font-medium text-right">Data</th>
                </tr>
              </thead>
              <tbody>
                {effectiveItens.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => navigate(`/consumo-interno/${item.consumidor_id}`)}
                    className="cursor-pointer border-b transition-colors hover:bg-gray-50"
                  >
                    <td className="py-3 font-medium">{item.consumidor_nome}</td>
                    <td className="py-3">
                      <div>{item.produto_nome}</div>
                      {item.observacao && <div className="text-xs text-gray-400">{item.observacao}</div>}
                    </td>
                    <td className="py-3 text-center">{formatQuantidade(item.quantidade)}</td>
                    <td className="py-3 text-right">{formatCurrency(Number(item.custo_unitario))}</td>
                    <td className="py-3 text-right font-medium">{formatCurrency(Number(item.subtotal))}</td>
                    <td className="py-3 text-right text-gray-500">{fmtData(item.created_at)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t-2">
                  <td colSpan={4} className="pt-3 font-semibold">Total</td>
                  <td className="pt-3 text-right font-semibold">
                    {formatCurrency(effectiveItens.reduce((a, i) => a + Number(i.subtotal), 0))}
                  </td>
                  <td />
                </tr>
              </tfoot>
            </table>
          </div>

          <div className="space-y-2 sm:hidden">
            {effectiveItens.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => navigate(`/consumo-interno/${item.consumidor_id}`)}
                className="w-full rounded border p-3 text-left transition-colors hover:bg-gray-50"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-medium">{item.produto_nome}</div>
                    <div className="text-xs text-gray-500">{item.consumidor_nome}</div>
                    {item.observacao && <div className="text-xs text-gray-400">{item.observacao}</div>}
                    <div className="mt-1 text-xs text-gray-500">
                      {formatQuantidade(item.quantidade)} × {formatCurrency(Number(item.custo_unitario))} · {fmtData(item.created_at)}
                    </div>
                  </div>
                  <span className="font-semibold">{formatCurrency(Number(item.subtotal))}</span>
                </div>
              </button>
            ))}
            <div className="rounded bg-gray-50 p-3 text-right font-semibold">
              Total: {formatCurrency(effectiveItens.reduce((a, i) => a + Number(i.subtotal), 0))}
            </div>
          </div>
        </>
      )}

      <LancarConsumoModal open={showModal} onClose={() => setShowModal(false)} />
    </div>
  );
}
