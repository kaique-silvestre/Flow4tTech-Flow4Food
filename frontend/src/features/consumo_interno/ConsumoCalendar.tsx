import { useMemo } from "react";
import { formatCurrency, parseApiDate } from "@/lib/format";
import type { ItemConsumoInternoResponse } from "./useConsumoInterno";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type PeriodMode = "semana" | "mes" | "ano";

interface DayData {
  total: number;
  count: number;
}

interface Props {
  items: ItemConsumoInternoResponse[];
  periodMode: PeriodMode;
  anchor: Date;
  selectedDay: string | null;
  onDaySelect: (day: string | null) => void;
  onMonthNavigate: (year: number, month: number) => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const WEEK_HEADERS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];
const MESES_SHORT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

function toIsoDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function isToday(d: Date): boolean {
  const t = new Date();
  return d.getDate() === t.getDate() && d.getMonth() === t.getMonth() && d.getFullYear() === t.getFullYear();
}

function localDateKey(isoUtc: string): string {
  const d = parseApiDate(isoUtc);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function aggregateByDay(items: ItemConsumoInternoResponse[]): Map<string, DayData> {
  const map = new Map<string, DayData>();
  for (const item of items) {
    const day = localDateKey(item.created_at);
    const prev = map.get(day) ?? { total: 0, count: 0 };
    map.set(day, { total: prev.total + Number(item.subtotal), count: prev.count + 1 });
  }
  return map;
}

function getMonthDays(year: number, month: number): (Date | null)[] {
  const firstDay = new Date(year, month - 1, 1);
  const lastDay = new Date(year, month, 0);
  let startDow = firstDay.getDay() - 1;
  if (startDow < 0) startDow = 6;
  const days: (Date | null)[] = Array(startDow).fill(null);
  for (let d = 1; d <= lastDay.getDate(); d++) days.push(new Date(year, month - 1, d));
  while (days.length % 7 !== 0) days.push(null);
  return days;
}

// ---------------------------------------------------------------------------
// Month calendar (full + compact variants)
// ---------------------------------------------------------------------------

function MonthCalendar({
  year,
  month,
  dayMap,
  selectedDay,
  onDaySelect,
  compact = false,
}: {
  year: number;
  month: number;
  dayMap: Map<string, DayData>;
  selectedDay: string | null;
  onDaySelect: (day: string | null) => void;
  compact?: boolean;
}) {
  const days = getMonthDays(year, month);
  const maxTotal = useMemo(() => {
    let max = 0;
    for (const [, v] of dayMap) if (v.total > max) max = v.total;
    return max;
  }, [dayMap]);

  return (
    <div>
      <div className="grid grid-cols-7 mb-1">
        {WEEK_HEADERS.map((h) => (
          <div
            key={h}
            className={`text-center font-medium text-gray-400 ${compact ? "text-[9px] py-0.5" : "text-xs py-1"}`}
          >
            {compact ? h.charAt(0) : h}
          </div>
        ))}
      </div>
      <div className={`grid grid-cols-7 ${compact ? "gap-px" : "gap-0.5"}`}>
        {days.map((d, i) => {
          if (!d) return <div key={`pad-${i}`} className={compact ? "h-5" : "min-h-[56px]"} />;

          const iso = toIsoDate(d);
          const data = dayMap.get(iso);
          const isSelected = selectedDay === iso;
          const today = isToday(d);
          const intensity = data && maxTotal > 0 ? data.total / maxTotal : 0;

          let bgClass = "";
          if (isSelected) bgClass = "bg-gray-900";
          else if (data) {
            if (intensity > 0.66) bgClass = "bg-blue-200 hover:bg-blue-300";
            else if (intensity > 0.33) bgClass = "bg-blue-100 hover:bg-blue-200";
            else bgClass = "bg-blue-50 hover:bg-blue-100";
          } else {
            bgClass = "hover:bg-gray-50";
          }

          if (compact) {
            return (
              <button
                key={iso}
                type="button"
                onClick={() => onDaySelect(isSelected ? null : iso)}
                className={`flex flex-col items-center justify-center rounded transition-colors h-5 ${bgClass} ${today && !isSelected ? "ring-1 ring-blue-400" : ""}`}
              >
                <span className={`text-[9px] leading-none ${isSelected ? "text-white" : today ? "text-blue-600 font-bold" : "text-gray-700"}`}>
                  {d.getDate()}
                </span>
                {data && !isSelected && (
                  <span className="w-1 h-1 rounded-full bg-blue-400 mt-px" />
                )}
              </button>
            );
          }

          return (
            <button
              key={iso}
              type="button"
              onClick={() => data && onDaySelect(isSelected ? null : iso)}
              className={`rounded p-1.5 flex flex-col transition-colors min-h-[56px] text-left ${bgClass} ${!data ? "cursor-default" : "cursor-pointer"} ${today && !isSelected ? "ring-1 ring-inset ring-blue-400" : ""}`}
            >
              <span className={`text-xs font-medium ${isSelected ? "text-white" : today ? "text-blue-600" : "text-gray-700"}`}>
                {d.getDate()}
              </span>
              {data && (
                <span className={`text-[10px] leading-tight mt-0.5 font-medium ${isSelected ? "text-blue-100" : "text-gray-700"}`}>
                  {formatCurrency(data.total)}
                </span>
              )}
              {data && (
                <span className={`text-[10px] leading-tight ${isSelected ? "text-blue-200" : "text-gray-400"}`}>
                  {data.count} {data.count === 1 ? "item" : "itens"}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Week calendar
// ---------------------------------------------------------------------------

function WeekCalendar({
  anchor,
  dayMap,
  selectedDay,
  onDaySelect,
}: {
  anchor: Date;
  dayMap: Map<string, DayData>;
  selectedDay: string | null;
  onDaySelect: (day: string | null) => void;
}) {
  const days = useMemo(() => {
    const start = new Date(anchor);
    const dow = start.getDay();
    start.setDate(start.getDate() + (dow === 0 ? -6 : 1 - dow));
    start.setHours(0, 0, 0, 0);
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(start);
      d.setDate(d.getDate() + i);
      return d;
    });
  }, [anchor]);

  return (
    <div className="grid grid-cols-7 gap-1">
      {days.map((d) => {
        const iso = toIsoDate(d);
        const data = dayMap.get(iso);
        const isSelected = selectedDay === iso;
        const today = isToday(d);

        let bgClass = "";
        if (isSelected) bgClass = "bg-gray-900 border-gray-900";
        else if (data) bgClass = "bg-blue-50 hover:bg-blue-100 border-blue-200";
        else bgClass = "hover:bg-gray-50 border-gray-100";

        return (
          <button
            key={iso}
            type="button"
            onClick={() => data && onDaySelect(isSelected ? null : iso)}
            className={`rounded border p-2 flex flex-col items-center transition-colors min-h-[80px] ${bgClass} ${!data ? "cursor-default" : "cursor-pointer"} ${today && !isSelected ? "ring-2 ring-blue-400" : ""}`}
          >
            <span className={`text-[11px] font-medium ${isSelected ? "text-gray-400" : "text-gray-400"}`}>
              {WEEK_HEADERS[d.getDay() === 0 ? 6 : d.getDay() - 1]}
            </span>
            <span className={`text-xl font-bold leading-tight mt-0.5 ${isSelected ? "text-white" : today ? "text-blue-600" : "text-gray-800"}`}>
              {d.getDate()}
            </span>
            {data ? (
              <>
                <span className={`text-xs font-medium mt-1 ${isSelected ? "text-blue-100" : "text-gray-700"}`}>
                  {formatCurrency(data.total)}
                </span>
                <span className={`text-[11px] mt-0.5 ${isSelected ? "text-blue-200" : "text-gray-400"}`}>
                  {data.count} {data.count === 1 ? "item" : "itens"}
                </span>
              </>
            ) : (
              <span className="text-xs text-gray-300 mt-2">—</span>
            )}
          </button>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Year calendar (12 mini months)
// ---------------------------------------------------------------------------

function YearCalendar({
  year,
  dayMap,
  selectedDay,
  onDaySelect,
  onMonthNavigate,
}: {
  year: number;
  dayMap: Map<string, DayData>;
  selectedDay: string | null;
  onDaySelect: (day: string | null) => void;
  onMonthNavigate: (year: number, month: number) => void;
}) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
      {Array.from({ length: 12 }, (_, i) => i + 1).map((month) => {
        const prefix = `${year}-${String(month).padStart(2, "0")}`;
        const monthMap = new Map<string, DayData>();
        for (const [k, v] of dayMap) {
          if (k.startsWith(prefix)) monthMap.set(k, v);
        }
        const monthTotal = Array.from(monthMap.values()).reduce((s, v) => s + v.total, 0);

        return (
          <div key={month} className="rounded border bg-white p-2">
            <button
              type="button"
              onClick={() => onMonthNavigate(year, month)}
              className="w-full text-left mb-1.5 flex items-center justify-between group"
            >
              <span className="text-xs font-semibold text-gray-700 group-hover:text-blue-600 transition-colors">
                {MESES_SHORT[month - 1]}
              </span>
              {monthTotal > 0 && (
                <span className="text-[10px] text-gray-400 group-hover:text-blue-500 transition-colors">
                  {formatCurrency(monthTotal)}
                </span>
              )}
            </button>
            <MonthCalendar
              year={year}
              month={month}
              dayMap={monthMap}
              selectedDay={selectedDay}
              onDaySelect={onDaySelect}
              compact
            />
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main export
// ---------------------------------------------------------------------------

export function ConsumoCalendar({
  items,
  periodMode,
  anchor,
  selectedDay,
  onDaySelect,
  onMonthNavigate,
}: Props) {
  const dayMap = useMemo(() => aggregateByDay(items), [items]);

  return (
    <div className="rounded border bg-white p-4 mb-4">
      {periodMode === "mes" && (
        <MonthCalendar
          year={anchor.getFullYear()}
          month={anchor.getMonth() + 1}
          dayMap={dayMap}
          selectedDay={selectedDay}
          onDaySelect={onDaySelect}
        />
      )}
      {periodMode === "semana" && (
        <WeekCalendar
          anchor={anchor}
          dayMap={dayMap}
          selectedDay={selectedDay}
          onDaySelect={onDaySelect}
        />
      )}
      {periodMode === "ano" && (
        <YearCalendar
          year={anchor.getFullYear()}
          dayMap={dayMap}
          selectedDay={selectedDay}
          onDaySelect={onDaySelect}
          onMonthNavigate={onMonthNavigate}
        />
      )}
    </div>
  );
}
