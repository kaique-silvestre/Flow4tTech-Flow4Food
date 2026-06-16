import { useState, useMemo, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  ChevronLeft,
  ChevronRight,
  Plus,
  Calendar,
  Clock,
  Grid3X3,
  List,
  Search,
  Filter,
  X,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  useEventos,
  useCreateEvento,
  usePatchEvento,
  useDeleteEvento,
  type EventoResponse,
} from "./useEventos";
import { usePromocoesMes, type PromoçaoResponse } from "@/features/cadastros/promocoes/usePromocoes";
import { useConsolidado, type CockpitItem } from "./useConsolidado";

// ── types ──────────────────────────────────────────────────────────────────

type Tipo = "evento" | "promocao" | "conta_pagar" | "entrega_insumo";
type View = "month" | "week" | "day" | "list";

interface CalItem {
  id: string;
  tipo: Tipo;
  label: string;
  descricao?: string;
  dateStr: string;
  horaInicio?: string; // HH:MM
  horaFim?: string;    // HH:MM
  itens?: string[];
  rawEvento?: EventoResponse;
  rawCockpit?: CockpitItem;
}

// ── helpers ────────────────────────────────────────────────────────────────

function todayMes(): string {
  const n = new Date();
  return `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, "0")}`;
}
function prevMes(m: string): string {
  const [y, mo] = m.split("-").map(Number);
  const d = new Date(y, mo - 2, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}
function nextMes(m: string): string {
  const [y, mo] = m.split("-").map(Number);
  const d = new Date(y, mo, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}
function mesLabel(m: string): string {
  const [y, mo] = m.split("-").map(Number);
  return new Date(y, mo - 1, 1).toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
}
function dateToStr(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function isPromoAtiva(p: PromoçaoResponse, date: Date): boolean {
  const d = dateToStr(date);
  if (d < p.data_inicio) return false;
  if (p.data_fim && d > p.data_fim) return false;
  if (p.recorrencia === "semanal" && p.dias_semana) return p.dias_semana.includes(date.getDay());
  if (p.recorrencia === "mensal" && p.dias_mes) return p.dias_mes.includes(date.getDate());
  return true;
}
function fmtBRL(v: number | null): string {
  if (v == null) return "";
  return Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
function fmtHora(h: string): string {
  return h.slice(0, 5);
}

// Convert "HH:MM" to fractional hours (e.g. "10:30" → 10.5)
function timeToFrac(hhmm: string): number {
  const [h, m] = hhmm.split(":").map(Number);
  return h + m / 60;
}

/** Compute absolute top + height for a timed item within the time grid */
function getItemStyle(item: CalItem, rowHeight: number): { top: number; height: number } | null {
  if (!item.horaInicio) return null;
  const start = timeToFrac(item.horaInicio);
  const end = item.horaFim ? timeToFrac(item.horaFim) : start + 1;
  const duration = Math.max(end - start, 0.25); // minimum 15 min
  return {
    top: start * rowHeight,
    height: duration * rowHeight,
  };
}

/** Layout overlapping timed items into side-by-side columns */
function layoutTimedItems(items: CalItem[]): Array<{ item: CalItem; col: number; totalCols: number }> {
  const sorted = [...items].sort((a, b) => (a.horaInicio ?? "").localeCompare(b.horaInicio ?? ""));
  // Each entry in `cols` tracks end time of last item placed in that column
  const cols: string[] = [];
  const colAssign: number[] = [];

  for (const item of sorted) {
    const start = item.horaInicio ?? "00:00";
    const end = item.horaFim ?? `${String(Math.min(23, parseInt(start) + 1)).padStart(2, "0")}:00`;
    let placed = -1;
    for (let i = 0; i < cols.length; i++) {
      if (cols[i] <= start) { cols[i] = end; placed = i; break; }
    }
    if (placed === -1) { placed = cols.length; cols.push(end); }
    colAssign.push(placed);
  }

  const totalCols = cols.length || 1;
  return sorted.map((item, i) => ({ item, col: colAssign[i], totalCols }));
}

const TIPO_STYLE: Record<Tipo, { bg: string; text: string; border: string; dot: string }> = {
  evento:         { bg: "bg-blue-100",   text: "text-blue-800",   border: "border-l-2 border-blue-500",   dot: "bg-blue-500" },
  promocao:       { bg: "bg-green-100",  text: "text-green-800",  border: "border-l-2 border-green-500",  dot: "bg-green-500" },
  conta_pagar:    { bg: "bg-red-100",    text: "text-red-800",    border: "border-l-2 border-red-500",    dot: "bg-red-500" },
  entrega_insumo: { bg: "bg-yellow-100", text: "text-yellow-800", border: "border-l-2 border-yellow-500", dot: "bg-yellow-500" },
};
const TIPO_LABEL: Record<Tipo, string> = {
  evento: "Eventos",
  promocao: "Promoções",
  conta_pagar: "Contas a Pagar",
  entrega_insumo: "Entregas",
};
const WEEK_DAYS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

// ── inline chip (month / list / all-day strip) ─────────────────────────────

function Chip({
  item, onClick, onDelete,
}: { item: CalItem; onClick?: () => void; onDelete?: () => void }) {
  const s = TIPO_STYLE[item.tipo];
  return (
    <div
      className={cn("group flex items-center justify-between rounded px-1.5 py-0.5 text-xs font-medium truncate cursor-pointer", s.bg, s.text)}
      onClick={onClick}
      title={item.descricao ?? item.label}
    >
      <span className="truncate">{item.label}</span>
      {onDelete && (
        <button type="button" className="ml-1 shrink-0 opacity-0 group-hover:opacity-100 hover:text-red-600"
          onClick={(e) => { e.stopPropagation(); onDelete(); }}>×</button>
      )}
    </div>
  );
}

// ── block chip (week/day absolute blocks) ──────────────────────────────────

function BlockChip({
  item, onClick, onDelete,
}: { item: CalItem; onClick?: () => void; onDelete?: () => void }) {
  const s = TIPO_STYLE[item.tipo];
  return (
    <div
      className={cn(
        "group relative h-full w-full rounded px-1.5 py-1 text-xs font-medium cursor-pointer overflow-hidden",
        s.bg, s.text, s.border,
      )}
      onClick={onClick}
      title={item.descricao ?? item.label}
    >
      <div className="font-semibold truncate leading-tight">{item.label}</div>
      {item.horaInicio && (
        <div className="opacity-70 text-[10px] mt-0.5 leading-none">
          {item.horaInicio}{item.horaFim ? `–${item.horaFim}` : ""}
        </div>
      )}
      {item.itens && item.itens.length > 0 && (
        <div className="opacity-60 text-[9px] mt-0.5 truncate">{item.itens.join(", ")}</div>
      )}
      {onDelete && (
        <button
          type="button"
          className="absolute top-0.5 right-0.5 opacity-0 group-hover:opacity-100 hover:text-red-600 leading-none"
          onClick={(e) => { e.stopPropagation(); onDelete(); }}
        >×</button>
      )}
    </div>
  );
}

// ── main page ──────────────────────────────────────────────────────────────

export function CalendarioPage() {
  const navigate = useNavigate();
  const [mesAtual, setMesAtual] = useState(todayMes);
  const [view, setView] = useState<View>("month");
  const [weekStart, setWeekStart] = useState<string>(() => {
    const today = new Date();
    today.setDate(today.getDate() - today.getDay());
    return dateToStr(today);
  });
  const [busca, setBusca] = useState("");
  const [visibleTipos, setVisibleTipos] = useState<Set<Tipo>>(
    new Set(["evento", "promocao", "conta_pagar", "entrega_insumo"] as Tipo[]),
  );
  const [rowHeight, setRowHeight] = useState(64);

  const { data: eventos = [], isLoading } = useEventos(mesAtual);
  const { data: promocoes = [] } = usePromocoesMes(mesAtual);
  const { data: consolidado = [] } = useConsolidado(mesAtual);
  const createMut = useCreateEvento();
  const patchMut = usePatchEvento();
  const deleteMut = useDeleteEvento();

  const [modal, setModal] = useState<{ open: boolean; editing: EventoResponse | null; dateFixa: string }>({
    open: false, editing: null, dateFixa: "",
  });
  const [titulo, setTitulo] = useState("");
  const [descricao, setDescricao] = useState("");
  const [dataInput, setDataInput] = useState("");
  const [horaInicioInput, setHoraInicioInput] = useState("");
  const [horaFimInput, setHoraFimInput] = useState("");

  const [detail, setDetail] = useState<{ open: boolean; item: CalItem | null }>({ open: false, item: null });
  const [confirmEvento, setConfirmEvento] = useState<EventoResponse | null>(null);
  const [currentDay, setCurrentDay] = useState<string>(dateToStr(new Date()));

  const [year, month] = mesAtual.split("-").map(Number);

  // ── build calendar items ──

  const allItems = useMemo<CalItem[]>(() => {
    const items: CalItem[] = [];

    for (const ev of eventos) {
      items.push({
        id: `ev-${ev.id}`,
        tipo: "evento",
        label: ev.titulo,
        descricao: ev.descricao ?? undefined,
        dateStr: ev.data_evento,
        horaInicio: ev.hora_inicio ? fmtHora(ev.hora_inicio) : undefined,
        horaFim: ev.hora_fim ? fmtHora(ev.hora_fim) : undefined,
        rawEvento: ev,
      });
    }

    const daysInMonth: Date[] = [];
    const start = new Date(year, month - 1, 1);
    while (start.getMonth() === month - 1) {
      daysInMonth.push(new Date(start));
      start.setDate(start.getDate() + 1);
    }
    for (const p of promocoes) {
      for (const day of daysInMonth) {
        if (!isPromoAtiva(p, day)) continue;
        const ds = dateToStr(day);
        const hi = p.hora_inicio?.slice(0, 5);
        const hf = p.hora_fim?.slice(0, 5);
        const isAllDay = !hi || (hi === "00:00" && (!hf || hf >= "23:00"));
        items.push({
          id: `pr-${p.id}-${ds}`,
          tipo: "promocao",
          label: p.nome,
          descricao: `${p.tipo_desconto === "porcentagem" ? p.valor_desconto + "%" : "R$ " + p.valor_desconto} · ${hi ?? "00:00"}–${hf ?? "23:59"}`,
          dateStr: ds,
          horaInicio: isAllDay ? undefined : hi,
          horaFim: isAllDay ? undefined : hf,
        });
      }
    }

    for (const ci of consolidado) {
      if (ci.tipo !== "conta_pagar" && ci.tipo !== "entrega_insumo") continue;

      let label: string;
      if (ci.tipo === "conta_pagar") {
        const valorStr = fmtBRL(ci.valor);
        label = valorStr
          ? `${valorStr} · ${ci.fornecedor_nome ?? "Sem fornecedor"}`
          : ci.fornecedor_nome ?? "Sem fornecedor";
      } else {
        if (ci.itens && ci.itens.length > 0) {
          const preview = ci.itens.slice(0, 2).join(", ");
          label = ci.itens.length > 2 ? `${preview} +${ci.itens.length - 2}` : preview;
        } else {
          label = ci.fornecedor_nome ?? "Entrega";
        }
      }

      items.push({
        id: `ci-${ci.tipo}-${ci.referencia_id}`,
        tipo: ci.tipo as Tipo,
        label,
        descricao: ci.fornecedor_nome ?? ci.descricao,
        dateStr: ci.data_referencia,
        horaInicio: ci.hora_inicio ? ci.hora_inicio.slice(0, 5) : undefined,
        horaFim: ci.hora_fim ? ci.hora_fim.slice(0, 5) : undefined,
        itens: ci.itens ?? [],
        rawCockpit: ci,
      });
    }

    return items;
  }, [eventos, promocoes, consolidado, year, month]);

  const filtered = useMemo(() => {
    return allItems.filter((item) => {
      if (!visibleTipos.has(item.tipo)) return false;
      if (busca) {
        const q = busca.toLowerCase();
        if (!item.label.toLowerCase().includes(q) && !item.descricao?.toLowerCase().includes(q)) return false;
      }
      return true;
    });
  }, [allItems, visibleTipos, busca]);

  const presentTipos = useMemo(() => {
    const set = new Set<Tipo>(["evento", "promocao"]);
    for (const ci of consolidado) {
      if (ci.tipo === "conta_pagar" || ci.tipo === "entrega_insumo") set.add(ci.tipo as Tipo);
    }
    return set;
  }, [consolidado]);

  function toggleTipo(t: Tipo) {
    setVisibleTipos((prev) => {
      const next = new Set(prev);
      if (next.has(t)) { next.delete(t); } else { next.add(t); }
      return next;
    });
  }

  // ── modal helpers ──

  function openCreate(ds: string, horaInicio?: string, horaFim?: string) {
    setModal({ open: true, editing: null, dateFixa: ds });
    setTitulo("");
    setDescricao("");
    setDataInput(ds);
    setHoraInicioInput(horaInicio ?? "");
    setHoraFimInput(horaFim ?? "");
  }
  function openEdit(ev: EventoResponse) {
    setModal({ open: true, editing: ev, dateFixa: "" });
    setTitulo(ev.titulo);
    setDescricao(ev.descricao ?? "");
    setDataInput(ev.data_evento);
    setHoraInicioInput(ev.hora_inicio ? fmtHora(ev.hora_inicio) : "");
    setHoraFimInput(ev.hora_fim ? fmtHora(ev.hora_fim) : "");
  }
  function closeModal() {
    setModal({ open: false, editing: null, dateFixa: "" });
  }
  function handleSave() {
    if (!titulo.trim() || !dataInput) return;
    const horaInicio = horaInicioInput || null;
    const horaFim = horaFimInput || null;
    if (modal.editing) {
      patchMut.mutate({ id: modal.editing.id, data: { titulo: titulo.trim(), descricao: descricao || null, hora_inicio: horaInicio, hora_fim: horaFim } }, { onSuccess: closeModal });
    } else {
      createMut.mutate({ titulo: titulo.trim(), descricao: descricao || null, data_evento: dataInput, hora_inicio: horaInicio, hora_fim: horaFim }, { onSuccess: closeModal });
    }
  }

  function handleChipClick(item: CalItem) {
    if (item.tipo === "evento" && item.rawEvento) { openEdit(item.rawEvento); return; }
    setDetail({ open: true, item });
  }
  function handleChipDelete(item: CalItem) {
    if (item.tipo === "evento" && item.rawEvento) setConfirmEvento(item.rawEvento);
  }

  const byDate = useMemo<Record<string, CalItem[]>>(() => {
    return filtered.reduce<Record<string, CalItem[]>>((acc, item) => {
      (acc[item.dateStr] ??= []).push(item);
      return acc;
    }, {});
  }, [filtered]);

  // ── navigation ──

  const viewLabel = {
    month: mesLabel(mesAtual),
    week: (() => {
      const ws = new Date(weekStart + "T12:00:00");
      const we = new Date(weekStart + "T12:00:00");
      we.setDate(we.getDate() + 6);
      return `Semana De ${ws.toLocaleDateString("pt-BR", { day: "numeric", month: "short" })} – ${we.toLocaleDateString("pt-BR", { day: "numeric", month: "short" })}`;
    })(),
    day: new Date(currentDay + "T12:00:00").toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long", year: "numeric" }),
    list: "Todos os Eventos",
  }[view];

  function shiftWeek(ws: string, delta: number): string {
    const d = new Date(ws + "T12:00:00");
    d.setDate(d.getDate() + delta);
    return dateToStr(d);
  }
  function weekMes(ws: string): string {
    const d = new Date(ws + "T12:00:00");
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  }

  function navPrev() {
    if (view === "month" || view === "list") setMesAtual(prevMes);
    else if (view === "week") setWeekStart((p) => { const n = shiftWeek(p, -7); setMesAtual(weekMes(n)); return n; });
    else if (view === "day") { const d = new Date(currentDay + "T12:00:00"); d.setDate(d.getDate() - 1); setCurrentDay(dateToStr(d)); }
  }
  function navNext() {
    if (view === "month" || view === "list") setMesAtual(nextMes);
    else if (view === "week") setWeekStart((p) => { const n = shiftWeek(p, 7); setMesAtual(weekMes(n)); return n; });
    else if (view === "day") { const d = new Date(currentDay + "T12:00:00"); d.setDate(d.getDate() + 1); setCurrentDay(dateToStr(d)); }
  }
  function navToday() {
    const today = new Date();
    const sun = new Date(today);
    sun.setDate(today.getDate() - today.getDay());
    setMesAtual(todayMes());
    setCurrentDay(dateToStr(today));
    setWeekStart(dateToStr(sun));
  }

  const todayStr = dateToStr(new Date());

  const handleCreateWithTime = useCallback((ds: string, h1: number, h2: number) => {
    const pad = (n: number) => String(n).padStart(2, "0");
    openCreate(ds, `${pad(h1)}:00`, `${pad(Math.min(h2, 23))}:00`);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── render ──

  return (
    <div className="p-4 lg:p-6 flex flex-col gap-4">
      {/* header */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
          <h2 className="text-xl font-semibold sm:text-2xl capitalize">{viewLabel}</h2>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" onClick={navPrev} className="h-8 w-8"><ChevronLeft className="h-4 w-4" /></Button>
            <Button variant="outline" size="sm" onClick={navToday}>Hoje</Button>
            <Button variant="outline" size="icon" onClick={navNext} className="h-8 w-8"><ChevronRight className="h-4 w-4" /></Button>
          </div>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          {(view === "week" || view === "day") && (
            <div className="flex items-center gap-1 rounded-lg border bg-background p-1">
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setRowHeight((h) => Math.max(32, h - 16))}>
                <ZoomOut className="h-3.5 w-3.5" />
              </Button>
              <span className="text-xs text-muted-foreground px-1">{rowHeight}px</span>
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setRowHeight((h) => Math.min(160, h + 16))}>
                <ZoomIn className="h-3.5 w-3.5" />
              </Button>
            </div>
          )}
          <div className="hidden sm:flex items-center gap-1 rounded-lg border bg-background p-1">
            {(["month", "week", "day", "list"] as View[]).map((v) => {
              const icons = { month: Calendar, week: Grid3X3, day: Clock, list: List };
              const labels = { month: "Mês", week: "Semana", day: "Dia", list: "Lista" };
              const Icon = icons[v];
              return (
                <Button key={v} variant={view === v ? "secondary" : "ghost"} size="sm" onClick={() => setView(v)} className="h-8">
                  <Icon className="h-4 w-4" /><span className="ml-1">{labels[v]}</span>
                </Button>
              );
            })}
          </div>
          <div className="sm:hidden flex gap-1 rounded-lg border bg-background p-1">
            {(["month", "week", "day", "list"] as View[]).map((v) => {
              const icons = { month: Calendar, week: Grid3X3, day: Clock, list: List };
              const Icon = icons[v];
              return (
                <Button key={v} variant={view === v ? "secondary" : "ghost"} size="sm" onClick={() => setView(v)} className="h-8 px-2">
                  <Icon className="h-4 w-4" />
                </Button>
              );
            })}
          </div>
          <Button onClick={() => openCreate(currentDay)} className="w-full sm:w-auto">
            <Plus className="mr-2 h-4 w-4" />Novo Evento
          </Button>
        </div>
      </div>

      {/* search + filters */}
      <div className="flex flex-col gap-2">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Buscar eventos..." value={busca} onChange={(e) => setBusca(e.target.value)} className="pl-9" />
          {busca && (
            <Button variant="ghost" size="icon" className="absolute right-1 top-1/2 h-7 w-7 -translate-y-1/2" onClick={() => setBusca("")}>
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2 bg-transparent">
                <Filter className="h-4 w-4" />Camadas
                {visibleTipos.size < presentTipos.size && (
                  <Badge variant="secondary" className="ml-1 h-5 px-1">{visibleTipos.size}/{presentTipos.size}</Badge>
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-52">
              <DropdownMenuLabel>Mostrar no calendário</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {(["evento", "promocao", "conta_pagar", "entrega_insumo"] as Tipo[]).filter((t) => presentTipos.has(t)).map((t) => (
                <DropdownMenuCheckboxItem key={t} checked={visibleTipos.has(t)} onCheckedChange={() => toggleTipo(t)}>
                  <div className="flex items-center gap-2">
                    <div className={cn("h-3 w-3 rounded", TIPO_STYLE[t].dot)} />{TIPO_LABEL[t]}
                  </div>
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
          {(["evento", "promocao", "conta_pagar", "entrega_insumo"] as Tipo[]).filter((t) => !visibleTipos.has(t) && presentTipos.has(t)).map((t) => (
            <Badge key={t} variant="outline" className="gap-1 cursor-pointer" onClick={() => toggleTipo(t)}>
              <div className={cn("h-2 w-2 rounded-full", TIPO_STYLE[t].dot)} />{TIPO_LABEL[t]} (oculto)<X className="h-3 w-3 ml-1" />
            </Badge>
          ))}
        </div>
      </div>

      {/* views */}
      {isLoading ? (
        <div className="h-96 animate-pulse rounded bg-gray-100" />
      ) : view === "month" ? (
        <MonthView year={year} month={month} byDate={byDate} todayStr={todayStr}
          onDayClick={(ds) => openCreate(ds)} onChipClick={handleChipClick} onChipDelete={handleChipDelete} />
      ) : view === "week" ? (
        <WeekView weekStart={weekStart} byDate={byDate} todayStr={todayStr} rowHeight={rowHeight}
          onDayClick={(ds) => openCreate(ds)} onChipClick={handleChipClick} onChipDelete={handleChipDelete}
          onCreateWithTime={handleCreateWithTime} />
      ) : view === "day" ? (
        <DayView dateStr={currentDay} byDate={byDate} rowHeight={rowHeight}
          onChipClick={handleChipClick} onChipDelete={handleChipDelete}
          onCreateWithTime={(h1, h2) => handleCreateWithTime(currentDay, h1, h2)} />
      ) : (
        <ListView filtered={filtered} todayStr={todayStr} onChipClick={handleChipClick} onChipDelete={handleChipDelete} />
      )}

      <ConfirmDialog
        open={confirmEvento !== null}
        title="Excluir evento?"
        description={confirmEvento ? `"${confirmEvento.titulo}" será excluído permanentemente.` : undefined}
        confirmLabel="Excluir"
        onConfirm={() => { deleteMut.mutate(confirmEvento!.id); setConfirmEvento(null); }}
        onCancel={() => setConfirmEvento(null)}
        isPending={deleteMut.isPending}
      />

      {/* create/edit modal */}
      <Dialog open={modal.open} onOpenChange={(v) => !v && closeModal()}>
        <DialogContent className="max-w-sm">
          <DialogHeader><DialogTitle>{modal.editing ? "Editar Evento" : "Novo Evento"}</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-sm text-gray-600">Data</label>
              <Input type="date" value={dataInput} onChange={(e) => setDataInput(e.target.value)} disabled={!!modal.dateFixa} />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="mb-1 block text-sm text-gray-600">Início</label>
                <Input type="time" value={horaInicioInput} onChange={(e) => setHoraInicioInput(e.target.value)} />
              </div>
              <div>
                <label className="mb-1 block text-sm text-gray-600">Fim</label>
                <Input type="time" value={horaFimInput} onChange={(e) => setHoraFimInput(e.target.value)} />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-600">Título</label>
              <Input value={titulo} onChange={(e) => setTitulo(e.target.value)} placeholder="Nome do evento" autoFocus />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-600">Descrição (opcional)</label>
              <textarea
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                rows={3} value={descricao} onChange={(e) => setDescricao(e.target.value)} placeholder="Detalhes do evento"
              />
            </div>
          </div>
          <DialogFooter>
            {modal.editing && (
              <Button variant="destructive" onClick={() => { setConfirmEvento(modal.editing!); closeModal(); }}>Excluir</Button>
            )}
            <Button variant="outline" onClick={closeModal}>Cancelar</Button>
            <Button onClick={handleSave} disabled={!titulo.trim() || !dataInput || createMut.isPending || patchMut.isPending}>Salvar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* detail modal */}
      <Dialog open={detail.open} onOpenChange={(v) => !v && setDetail({ open: false, item: null })}>
        {detail.item && (
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <div className={cn("h-3 w-3 rounded-full flex-shrink-0", TIPO_STYLE[detail.item.tipo].dot)} />
                {{ conta_pagar: "Conta a Pagar", entrega_insumo: "Entrega de Insumos", promocao: "Promoção", evento: "Evento" }[detail.item.tipo] ?? "Detalhe"}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-2 text-sm">
              {detail.item.tipo === "promocao" ? (
                <>
                  <div><span className="font-medium">Desconto: </span>{detail.item.descricao?.split(" · ")[0]}</div>
                  <div><span className="font-medium">Data: </span>{new Date(detail.item.dateStr + "T12:00:00").toLocaleDateString("pt-BR")}</div>
                  {detail.item.horaInicio && (
                    <div><span className="font-medium">Horário: </span>{detail.item.horaInicio}{detail.item.horaFim ? `–${detail.item.horaFim}` : ""}</div>
                  )}
                </>
              ) : (
                <>
                  {detail.item.rawCockpit?.valor != null && (
                    <div><span className="font-medium">Valor: </span>{fmtBRL(detail.item.rawCockpit.valor)}</div>
                  )}
                  {detail.item.rawCockpit?.fornecedor_nome
                    ? <div><span className="font-medium">Fornecedor: </span>{detail.item.rawCockpit.fornecedor_nome}</div>
                    : <div className="text-muted-foreground italic">Sem fornecedor vinculado</div>
                  }
                  {detail.item.itens && detail.item.itens.length > 0 && (
                    <div>
                      <span className="font-medium">Itens: </span>
                      <ul className="mt-1 ml-3 list-disc space-y-0.5 text-muted-foreground">
                        {detail.item.itens.map((nome) => <li key={nome}>{nome}</li>)}
                      </ul>
                    </div>
                  )}
                  <div><span className="font-medium">Data: </span>{new Date(detail.item.dateStr + "T12:00:00").toLocaleDateString("pt-BR")}</div>
                  {detail.item.horaInicio && (
                    <div><span className="font-medium">Horário: </span>{detail.item.horaInicio}{detail.item.horaFim ? `–${detail.item.horaFim}` : ""}</div>
                  )}
                </>
              )}
            </div>
            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => setDetail({ open: false, item: null })}>Fechar</Button>
              {detail.item.tipo === "conta_pagar" && (
                <Button onClick={() => { setDetail({ open: false, item: null }); navigate("/contas-pagar"); }}>Ir ao Financeiro</Button>
              )}
              {detail.item.tipo === "entrega_insumo" && (
                <Button onClick={() => { setDetail({ open: false, item: null }); navigate("/compras"); }}>Dar Entrada no Estoque</Button>
              )}
            </DialogFooter>
          </DialogContent>
        )}
      </Dialog>
    </div>
  );
}

// ── month view ─────────────────────────────────────────────────────────────

function MonthView({ year, month, byDate, todayStr, onDayClick, onChipClick, onChipDelete }: {
  year: number; month: number; byDate: Record<string, CalItem[]>; todayStr: string;
  onDayClick: (ds: string) => void;
  onChipClick: (item: CalItem) => void;
  onChipDelete: (item: CalItem) => void;
}) {
  const days: Date[] = [];
  const d = new Date(year, month - 1, 1);
  while (d.getMonth() === month - 1) { days.push(new Date(d)); d.setDate(d.getDate() + 1); }
  const firstDow = days[0].getDay();
  const cells: (Date | null)[] = [...Array<null>(firstDow).fill(null), ...days];
  while (cells.length % 7 !== 0) cells.push(null);

  return (
    <Card className="overflow-hidden">
      <div className="grid grid-cols-7 border-b bg-muted/30">
        {WEEK_DAYS.map((w) => (
          <div key={w} className="border-r py-2 text-center text-xs font-medium text-muted-foreground last:border-r-0">
            <span className="hidden sm:inline">{w}</span>
            <span className="sm:hidden">{w.charAt(0)}</span>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7">
        {cells.map((day, i) => {
          if (!day) return <div key={`e-${i}`} className="min-h-[90px] border-b border-r bg-muted/20 last:border-r-0" />;
          const ds = dateToStr(day);
          const items = byDate[ds] ?? [];
          const isToday = ds === todayStr;
          return (
            <div key={ds}
              className={cn("min-h-[90px] border-b border-r p-1 cursor-pointer transition-colors hover:bg-accent/50 last:border-r-0 sm:p-2",
                isToday && "bg-primary/5 ring-1 ring-inset ring-primary/30")}
              onClick={() => onDayClick(ds)}
            >
              <div className={cn("mb-1 flex h-6 w-6 items-center justify-center rounded-full text-xs sm:text-sm",
                isToday ? "bg-primary text-primary-foreground font-semibold" : "text-muted-foreground")}>
                {day.getDate()}
              </div>
              <div className="flex flex-col gap-0.5" onClick={(e) => e.stopPropagation()}>
                {items.slice(0, 3).map((item) => (
                  <Chip key={item.id} item={item}
                    onClick={() => onChipClick(item)}
                    onDelete={item.tipo === "evento" ? () => onChipDelete(item) : undefined} />
                ))}
                {items.length > 3 && <span className="text-[10px] text-muted-foreground">+{items.length - 3} mais</span>}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

// ── week view ──────────────────────────────────────────────────────────────

function WeekView({ weekStart, byDate, todayStr, rowHeight, onDayClick, onChipClick, onChipDelete, onCreateWithTime }: {
  weekStart: string; byDate: Record<string, CalItem[]>; todayStr: string; rowHeight: number;
  onDayClick: (ds: string) => void;
  onChipClick: (item: CalItem) => void;
  onChipDelete: (item: CalItem) => void;
  onCreateWithTime: (ds: string, h1: number, h2: number) => void;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const colRefs = useRef<(HTMLDivElement | null)[]>([]);
  const dragRef = useRef<{ ds: string; h1: number; h2: number } | null>(null);
  const [drag, setDrag] = useState<{ ds: string; h1: number; h2: number } | null>(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 8 * rowHeight;
  }, [weekStart, rowHeight]);

  useEffect(() => {
    function handleUp() {
      const d = dragRef.current;
      if (d) onCreateWithTime(d.ds, Math.min(d.h1, d.h2), Math.max(d.h1, d.h2) + 1);
      dragRef.current = null;
      setDrag(null);
    }
    window.addEventListener("mouseup", handleUp);
    return () => window.removeEventListener("mouseup", handleUp);
  }, [onCreateWithTime]);

  const weekDays: Date[] = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(weekStart + "T12:00:00");
    d.setDate(d.getDate() + i);
    return d;
  });

  function getHourAt(e: React.MouseEvent<HTMLDivElement>, colIdx: number): number {
    const el = colRefs.current[colIdx];
    if (!el) return 0;
    const rect = el.getBoundingClientRect();
    const y = e.clientY - rect.top;
    return Math.max(0, Math.min(23, Math.floor(y / rowHeight)));
  }

  const totalHeight = 24 * rowHeight;

  return (
    <Card className="overflow-hidden select-none">
      {/* header row */}
      <div className="grid border-b bg-background" style={{ gridTemplateColumns: "3rem repeat(7, 1fr)" }}>
        <div className="border-r p-2 text-center text-xs font-medium text-muted-foreground">Hora</div>
        {weekDays.map((day) => {
          const ds = dateToStr(day);
          const isToday = ds === todayStr;
          return (
            <div key={ds} className="border-r p-2 text-center text-xs font-medium last:border-r-0">
              <div className="hidden sm:block text-muted-foreground">{day.toLocaleDateString("pt-BR", { weekday: "short" })}</div>
              <div className={cn("mx-auto flex h-6 w-6 items-center justify-center rounded-full text-xs",
                isToday ? "bg-primary text-primary-foreground font-semibold" : "text-muted-foreground")}>
                {day.getDate()}
              </div>
            </div>
          );
        })}
      </div>

      {/* all-day strip */}
      <div className="grid border-b bg-muted/10" style={{ gridTemplateColumns: "3rem repeat(7, 1fr)" }}>
        <div className="border-r px-1 py-1 text-[10px] text-muted-foreground flex items-center justify-center">Dia todo</div>
        {weekDays.map((day) => {
          const ds = dateToStr(day);
          const isToday = ds === todayStr;
          const allDayItems = (byDate[ds] ?? []).filter((i) => !i.horaInicio);
          return (
            <div key={ds} className={cn("border-r p-0.5 last:border-r-0 min-h-8 space-y-0.5 cursor-pointer hover:bg-accent/30", isToday && "bg-primary/5")}
              onClick={() => onDayClick(ds)}>
              <div className="space-y-0.5" onClick={(e) => e.stopPropagation()}>
                {allDayItems.map((item) => (
                  <Chip key={item.id} item={item} onClick={() => onChipClick(item)}
                    onDelete={item.tipo === "evento" ? () => onChipDelete(item) : undefined} />
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* scrollable time grid */}
      <div ref={scrollRef} className="overflow-y-auto max-h-[600px]">
        <div className="flex" style={{ height: totalHeight }}>
          {/* hour labels */}
          <div className="w-12 flex-shrink-0 border-r relative" style={{ height: totalHeight }}>
            {HOURS.map((hour) => (
              <div key={hour} className="absolute left-0 right-0 border-b flex items-start px-1 pt-0.5 text-[9px] text-muted-foreground sm:text-[10px]"
                style={{ top: hour * rowHeight, height: rowHeight }}>
                {String(hour).padStart(2, "0")}:00
              </div>
            ))}
          </div>

          {/* day columns */}
          {weekDays.map((day, colIdx) => {
            const ds = dateToStr(day);
            const isToday = ds === todayStr;
            const timedItems = (byDate[ds] ?? []).filter((i) => i.horaInicio);
            const laid = layoutTimedItems(timedItems);
            const myDrag = drag?.ds === ds ? drag : null;

            return (
              <div
                key={ds}
                ref={(el) => { colRefs.current[colIdx] = el; }}
                className={cn("relative flex-1 border-r last:border-r-0 cursor-crosshair", isToday && "bg-primary/5")}
                style={{ height: totalHeight }}
                onMouseDown={(e) => {
                  const h = getHourAt(e, colIdx);
                  const state = { ds, h1: h, h2: h };
                  dragRef.current = state;
                  setDrag(state);
                }}
                onMouseMove={(e) => {
                  if (dragRef.current && dragRef.current.ds === ds) {
                    const h = getHourAt(e, colIdx);
                    const next = { ...dragRef.current, h2: h };
                    dragRef.current = next;
                    setDrag(next);
                  }
                }}
              >
                {/* hour grid lines */}
                {HOURS.map((hour) => (
                  <div key={hour} className="absolute left-0 right-0 border-b border-border/50"
                    style={{ top: hour * rowHeight, height: rowHeight }} />
                ))}

                {/* drag highlight */}
                {myDrag && (
                  <div className="absolute left-0 right-0 bg-blue-200/50 pointer-events-none z-0"
                    style={{
                      top: Math.min(myDrag.h1, myDrag.h2) * rowHeight,
                      height: (Math.abs(myDrag.h2 - myDrag.h1) + 1) * rowHeight,
                    }} />
                )}

                {/* timed events */}
                {laid.map(({ item, col, totalCols }) => {
                  const style = getItemStyle(item, rowHeight);
                  if (!style) return null;
                  const w = 100 / totalCols;
                  return (
                    <div
                      key={item.id}
                      className="absolute z-10 pr-0.5"
                      style={{ top: style.top, height: style.height, left: `${col * w}%`, width: `${w}%` }}
                      onMouseDown={(e) => e.stopPropagation()}
                    >
                      <BlockChip item={item} onClick={() => onChipClick(item)}
                        onDelete={item.tipo === "evento" ? () => onChipDelete(item) : undefined} />
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}

// ── day view ───────────────────────────────────────────────────────────────

function DayView({ dateStr, byDate, rowHeight, onChipClick, onChipDelete, onCreateWithTime }: {
  dateStr: string; byDate: Record<string, CalItem[]>; rowHeight: number;
  onChipClick: (item: CalItem) => void;
  onChipDelete: (item: CalItem) => void;
  onCreateWithTime: (h1: number, h2: number) => void;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<{ h1: number; h2: number } | null>(null);
  const [drag, setDrag] = useState<{ h1: number; h2: number } | null>(null);

  const items = byDate[dateStr] ?? [];
  const allDayItems = items.filter((i) => !i.horaInicio);
  const timedItems = items.filter((i) => i.horaInicio);
  const laid = layoutTimedItems(timedItems);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 8 * rowHeight;
  }, [dateStr, rowHeight]);

  useEffect(() => {
    function handleUp() {
      const d = dragRef.current;
      if (d) onCreateWithTime(Math.min(d.h1, d.h2), Math.max(d.h1, d.h2) + 1);
      dragRef.current = null;
      setDrag(null);
    }
    window.addEventListener("mouseup", handleUp);
    return () => window.removeEventListener("mouseup", handleUp);
  }, [onCreateWithTime]);

  function getHourAt(e: React.MouseEvent<HTMLDivElement>): number {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return 0;
    return Math.max(0, Math.min(23, Math.floor((e.clientY - rect.top) / rowHeight)));
  }

  const totalHeight = 24 * rowHeight;

  return (
    <Card className="overflow-hidden select-none">
      {allDayItems.length > 0 && (
        <div className="border-b bg-muted/10 p-2 flex gap-1 flex-wrap">
          <span className="text-xs text-muted-foreground mr-1 self-center">Dia todo:</span>
          {allDayItems.map((item) => (
            <Chip key={item.id} item={item} onClick={() => onChipClick(item)}
              onDelete={item.tipo === "evento" ? () => onChipDelete(item) : undefined} />
          ))}
        </div>
      )}
      <div ref={scrollRef} className="overflow-y-auto max-h-[600px]">
        <div className="flex" style={{ height: totalHeight }}>
          {/* hour labels */}
          <div className="w-14 sm:w-20 flex-shrink-0 border-r relative" style={{ height: totalHeight }}>
            {HOURS.map((hour) => (
              <div key={hour} className="absolute left-0 right-0 border-b flex items-start px-1 pt-0.5 text-[10px] text-muted-foreground sm:px-2 sm:text-xs"
                style={{ top: hour * rowHeight, height: rowHeight }}>
                {String(hour).padStart(2, "0")}:00
              </div>
            ))}
          </div>

          {/* events area */}
          <div
            ref={containerRef}
            className="relative flex-1 cursor-crosshair"
            style={{ height: totalHeight }}
            onMouseDown={(e) => {
              const h = getHourAt(e);
              const state = { h1: h, h2: h };
              dragRef.current = state;
              setDrag(state);
            }}
            onMouseMove={(e) => {
              if (dragRef.current) {
                const h = getHourAt(e);
                const next = { ...dragRef.current, h2: h };
                dragRef.current = next;
                setDrag(next);
              }
            }}
          >
            {/* hour grid lines */}
            {HOURS.map((hour) => (
              <div key={hour} className="absolute left-0 right-0 border-b border-border/50"
                style={{ top: hour * rowHeight, height: rowHeight }} />
            ))}

            {/* drag highlight */}
            {drag && (
              <div className="absolute left-0 right-0 bg-blue-200/50 pointer-events-none z-0"
                style={{
                  top: Math.min(drag.h1, drag.h2) * rowHeight,
                  height: (Math.abs(drag.h2 - drag.h1) + 1) * rowHeight,
                }} />
            )}

            {/* timed events */}
            {laid.map(({ item, col, totalCols }) => {
              const style = getItemStyle(item, rowHeight);
              if (!style) return null;
              const w = 100 / totalCols;
              return (
                <div
                  key={item.id}
                  className="absolute z-10 px-1"
                  style={{ top: style.top, height: style.height, left: `${col * w}%`, width: `${w}%` }}
                  onMouseDown={(e) => e.stopPropagation()}
                >
                  <BlockChip item={item} onClick={() => onChipClick(item)}
                    onDelete={item.tipo === "evento" ? () => onChipDelete(item) : undefined} />
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </Card>
  );
}

// ── list view ──────────────────────────────────────────────────────────────

function ListView({ filtered, todayStr, onChipClick, onChipDelete }: {
  filtered: CalItem[]; todayStr: string;
  onChipClick: (item: CalItem) => void;
  onChipDelete: (item: CalItem) => void;
}) {
  const sorted = [...filtered].sort((a, b) => a.dateStr.localeCompare(b.dateStr));
  const grouped = sorted.reduce<Record<string, CalItem[]>>((acc, item) => {
    (acc[item.dateStr] ??= []).push(item);
    return acc;
  }, {});

  if (sorted.length === 0) {
    return <Card className="p-8 text-center text-sm text-muted-foreground">Nenhum evento encontrado.</Card>;
  }

  return (
    <Card className="overflow-hidden">
      <div className="overflow-y-auto max-h-[600px] p-4">
        <div className="space-y-6">
          {Object.entries(grouped).map(([ds, items]) => {
            const label = new Date(ds + "T12:00:00").toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
            const isToday = ds === todayStr;
            return (
              <div key={ds} className="space-y-2">
                <h3 className={cn("text-sm font-semibold capitalize", isToday ? "text-primary" : "text-muted-foreground")}>
                  {label}{isToday && <span className="ml-2 text-xs font-normal">(hoje)</span>}
                </h3>
                <div className="space-y-1.5">
                  {items.map((item) => {
                    const s = TIPO_STYLE[item.tipo];
                    return (
                      <div key={item.id} onClick={() => onChipClick(item)}
                        className="group cursor-pointer rounded-lg border p-3 transition-all hover:shadow-md hover:scale-[1.01]">
                        <div className="flex items-start gap-3">
                          <div className={cn("mt-1 h-3 w-3 rounded-full flex-shrink-0", s.dot)} />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2">
                              <h4 className="font-medium text-sm group-hover:text-primary transition-colors">{item.label}</h4>
                              <div className="flex items-center gap-1 shrink-0">
                                <Badge variant="secondary" className="text-[10px]">{TIPO_LABEL[item.tipo]}</Badge>
                                {item.tipo === "evento" && (
                                  <button className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-red-600 transition-opacity"
                                    onClick={(e) => { e.stopPropagation(); onChipDelete(item); }}>
                                    <X className="h-3.5 w-3.5" />
                                  </button>
                                )}
                              </div>
                            </div>
                            {item.descricao && item.tipo !== "conta_pagar" && (
                              <p className="mt-0.5 text-xs text-muted-foreground line-clamp-2">{item.descricao}</p>
                            )}
                            {item.itens && item.itens.length > 0 && (
                              <p className="mt-0.5 text-xs text-muted-foreground">{item.itens.join(", ")}</p>
                            )}
                            {item.horaInicio && (
                              <div className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                                <Clock className="h-3 w-3" />{item.horaInicio}{item.horaFim ? `–${item.horaFim}` : ""}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}
