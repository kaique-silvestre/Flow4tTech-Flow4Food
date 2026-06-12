import { useState, useMemo, useRef, useEffect } from "react";
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
  dateStr: string; // YYYY-MM-DD
  horaInicio?: string; // HH:MM
  horaFim?: string;
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

const TIPO_STYLE: Record<Tipo, { bg: string; text: string; badge: string; dot: string }> = {
  evento:          { bg: "bg-blue-100",   text: "text-blue-800",   badge: "bg-blue-500",   dot: "bg-blue-500" },
  promocao:        { bg: "bg-green-100",  text: "text-green-800",  badge: "bg-green-500",  dot: "bg-green-500" },
  conta_pagar:     { bg: "bg-red-100",    text: "text-red-800",    badge: "bg-red-500",    dot: "bg-red-500" },
  entrega_insumo:  { bg: "bg-yellow-100", text: "text-yellow-800", badge: "bg-yellow-500", dot: "bg-yellow-500" },
};
const TIPO_LABEL: Record<Tipo, string> = {
  evento: "Eventos",
  promocao: "Promoções",
  conta_pagar: "Contas a Pagar",
  entrega_insumo: "Entregas",
};
const WEEK_DAYS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

// ── event chip ─────────────────────────────────────────────────────────────

function Chip({
  item,
  onEdit,
  onDelete,
  onClick,
}: {
  item: CalItem;
  onEdit?: () => void;
  onDelete?: () => void;
  onClick?: () => void;
}) {
  const s = TIPO_STYLE[item.tipo];
  return (
    <div
      className={cn(
        "group flex items-center justify-between rounded px-1.5 py-0.5 text-xs font-medium truncate cursor-pointer",
        s.bg, s.text,
      )}
      onClick={onClick ?? onEdit}
      title={item.descricao ?? item.label}
    >
      <span className="truncate">{item.label}</span>
      {onDelete && (
        <button
          type="button"
          className="ml-1 shrink-0 opacity-0 group-hover:opacity-100 hover:text-red-600"
          onClick={(e) => { e.stopPropagation(); onDelete(); }}
        >
          ×
        </button>
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

  const { data: eventos = [], isLoading } = useEventos(mesAtual);
  const { data: promocoes = [] } = usePromocoesMes(mesAtual);
  const { data: consolidado = [] } = useConsolidado(mesAtual);
  const createMut = useCreateEvento();
  const patchMut = usePatchEvento();
  const deleteMut = useDeleteEvento();

  // modal state
  const [modal, setModal] = useState<{ open: boolean; editing: EventoResponse | null; dateFixa: string }>({
    open: false, editing: null, dateFixa: "",
  });
  const [titulo, setTitulo] = useState("");
  const [descricao, setDescricao] = useState("");
  const [dataInput, setDataInput] = useState("");

  // detail modal for non-evento items
  const [detail, setDetail] = useState<{ open: boolean; item: CalItem | null }>({ open: false, item: null });

  // confirm delete evento
  const [confirmEvento, setConfirmEvento] = useState<EventoResponse | null>(null);

  // current day for day view
  const [currentDay, setCurrentDay] = useState<string>(dateToStr(new Date()));

  const [year, month] = mesAtual.split("-").map(Number);

  // ── build all calendar items ──

  const allItems = useMemo<CalItem[]>(() => {
    const items: CalItem[] = [];

    for (const ev of eventos) {
      items.push({
        id: `ev-${ev.id}`,
        tipo: "evento",
        label: ev.titulo,
        descricao: ev.descricao ?? undefined,
        dateStr: ev.data_evento,
        rawEvento: ev,
      });
    }

    // for promos: generate items for each day in current month where promo is active
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
        items.push({
          id: `pr-${p.id}-${ds}`,
          tipo: "promocao",
          label: p.nome,
          descricao: `${p.tipo_desconto === "porcentagem" ? p.valor_desconto + "%" : "R$ " + p.valor_desconto} · ${p.hora_inicio?.slice(0, 5) ?? "00:00"}–${p.hora_fim?.slice(0, 5) ?? "23:59"}`,
          dateStr: ds,
          horaInicio: p.hora_inicio?.slice(0, 5),
          horaFim: p.hora_fim?.slice(0, 5),
        });
      }
    }

    for (const ci of consolidado) {
      if (ci.tipo !== "conta_pagar" && ci.tipo !== "entrega_insumo") continue;
      items.push({
        id: `ci-${ci.tipo}-${ci.referencia_id}`,
        tipo: ci.tipo as Tipo,
        label: ci.descricao,
        descricao: ci.fornecedor_nome ?? ci.descricao,
        dateStr: ci.data_referencia,
        rawCockpit: ci,
      });
    }

    return items;
  }, [eventos, promocoes, consolidado, year, month]);

  // ── filter ──

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

  // ── present tipos (from consolidado permissions) ──
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

  function openCreate(ds: string) {
    setModal({ open: true, editing: null, dateFixa: ds });
    setTitulo("");
    setDescricao("");
    setDataInput(ds);
  }
  function openEdit(ev: EventoResponse) {
    setModal({ open: true, editing: ev, dateFixa: "" });
    setTitulo(ev.titulo);
    setDescricao(ev.descricao ?? "");
    setDataInput(ev.data_evento);
  }
  function closeModal() {
    setModal({ open: false, editing: null, dateFixa: "" });
  }
  function handleSave() {
    if (!titulo.trim() || !dataInput) return;
    if (modal.editing) {
      patchMut.mutate({ id: modal.editing.id, data: { titulo: titulo.trim(), descricao: descricao || null } }, { onSuccess: closeModal });
    } else {
      createMut.mutate({ titulo: titulo.trim(), descricao: descricao || null, data_evento: dataInput }, { onSuccess: closeModal });
    }
  }

  function handleChipClick(item: CalItem) {
    setDetail({ open: true, item });
  }
  function handleChipDelete(item: CalItem) {
    if (item.tipo === "evento" && item.rawEvento) {
      setConfirmEvento(item.rawEvento);
    }
  }

  // ── group by date ──
  const byDate = useMemo<Record<string, CalItem[]>>(() => {
    return filtered.reduce<Record<string, CalItem[]>>((acc, item) => {
      (acc[item.dateStr] ??= []).push(item);
      return acc;
    }, {});
  }, [filtered]);

  // ── navigation header ──

  const viewLabel = {
    month: mesLabel(mesAtual),
    week: (() => {
      const ws = new Date(weekStart + "T12:00:00");
      const we = new Date(weekStart + "T12:00:00");
      we.setDate(we.getDate() + 6);
      const sLabel = ws.toLocaleDateString("pt-BR", { day: "numeric", month: "short" });
      const eLabel = we.toLocaleDateString("pt-BR", { day: "numeric", month: "short" });
      return `Semana De ${sLabel} – ${eLabel}`;
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
    else if (view === "week") {
      setWeekStart((prev) => {
        const next = shiftWeek(prev, -7);
        setMesAtual(weekMes(next));
        return next;
      });
    } else if (view === "day") {
      const d = new Date(currentDay + "T12:00:00");
      d.setDate(d.getDate() - 1);
      setCurrentDay(dateToStr(d));
    }
  }
  function navNext() {
    if (view === "month" || view === "list") setMesAtual(nextMes);
    else if (view === "week") {
      setWeekStart((prev) => {
        const next = shiftWeek(prev, 7);
        setMesAtual(weekMes(next));
        return next;
      });
    } else if (view === "day") {
      const d = new Date(currentDay + "T12:00:00");
      d.setDate(d.getDate() + 1);
      setCurrentDay(dateToStr(d));
    }
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

  // ── render ──

  return (
    <div className="p-4 lg:p-6 flex flex-col gap-4">
      {/* ── header ── */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
          <h2 className="text-xl font-semibold sm:text-2xl capitalize">{viewLabel}</h2>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" onClick={navPrev} className="h-8 w-8">
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={navToday}>Hoje</Button>
            <Button variant="outline" size="icon" onClick={navNext} className="h-8 w-8">
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          {/* view toggles */}
          <div className="hidden sm:flex items-center gap-1 rounded-lg border bg-background p-1">
            {(["month", "week", "day", "list"] as View[]).map((v) => {
              const icons = { month: Calendar, week: Grid3X3, day: Clock, list: List };
              const labels = { month: "Mês", week: "Semana", day: "Dia", list: "Lista" };
              const Icon = icons[v];
              return (
                <Button key={v} variant={view === v ? "secondary" : "ghost"} size="sm" onClick={() => setView(v)} className="h-8">
                  <Icon className="h-4 w-4" />
                  <span className="ml-1">{labels[v]}</span>
                </Button>
              );
            })}
          </div>
          {/* mobile view select */}
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
            <Plus className="mr-2 h-4 w-4" />
            Novo Evento
          </Button>
        </div>
      </div>

      {/* ── search + filters ── */}
      <div className="flex flex-col gap-2">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar eventos..."
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            className="pl-9"
          />
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
                <Filter className="h-4 w-4" />
                Camadas
                {visibleTipos.size < presentTipos.size && (
                  <Badge variant="secondary" className="ml-1 h-5 px-1">{visibleTipos.size}/{presentTipos.size}</Badge>
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-52">
              <DropdownMenuLabel>Mostrar no calendário</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {(["evento", "promocao", "conta_pagar", "entrega_insumo"] as Tipo[])
                .filter((t) => presentTipos.has(t))
                .map((t) => (
                  <DropdownMenuCheckboxItem
                    key={t}
                    checked={visibleTipos.has(t)}
                    onCheckedChange={() => toggleTipo(t)}
                  >
                    <div className="flex items-center gap-2">
                      <div className={cn("h-3 w-3 rounded", TIPO_STYLE[t].dot)} />
                      {TIPO_LABEL[t]}
                    </div>
                  </DropdownMenuCheckboxItem>
                ))}
            </DropdownMenuContent>
          </DropdownMenu>
          {/* active filter badges */}
          {(["evento", "promocao", "conta_pagar", "entrega_insumo"] as Tipo[])
            .filter((t) => !visibleTipos.has(t) && presentTipos.has(t))
            .map((t) => (
              <Badge key={t} variant="outline" className="gap-1 cursor-pointer" onClick={() => toggleTipo(t)}>
                <div className={cn("h-2 w-2 rounded-full", TIPO_STYLE[t].dot)} />
                {TIPO_LABEL[t]} (oculto)
                <X className="h-3 w-3 ml-1" />
              </Badge>
            ))}
        </div>
      </div>

      {/* ── views ── */}
      {isLoading ? (
        <div className="h-96 animate-pulse rounded bg-gray-100" />
      ) : view === "month" ? (
        <MonthView
          year={year}
          month={month}
          byDate={byDate}
          todayStr={todayStr}
          onDayClick={(ds) => openCreate(ds)}
          onChipClick={handleChipClick}
          onChipDelete={handleChipDelete}
        />
      ) : view === "week" ? (
        <WeekView
          weekStart={weekStart}
          byDate={byDate}
          todayStr={todayStr}
          onDayClick={(ds) => openCreate(ds)}
          onChipClick={handleChipClick}
          onChipDelete={handleChipDelete}
        />
      ) : view === "day" ? (
        <DayView
          dateStr={currentDay}
          byDate={byDate}
          onChipClick={handleChipClick}
          onChipDelete={handleChipDelete}
        />
      ) : (
        <ListView
          filtered={filtered}
          todayStr={todayStr}
          onChipClick={handleChipClick}
          onChipDelete={handleChipDelete}
        />
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

      {/* ── create/edit evento modal ── */}
      <Dialog open={modal.open} onOpenChange={(v) => !v && closeModal()}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>{modal.editing ? "Editar Evento" : "Novo Evento"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-sm text-gray-600">Data</label>
              <Input type="date" value={dataInput} onChange={(e) => setDataInput(e.target.value)} disabled={!!modal.dateFixa} />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-600">Título</label>
              <Input value={titulo} onChange={(e) => setTitulo(e.target.value)} placeholder="Nome do evento" />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-600">Descrição (opcional)</label>
              <textarea
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                rows={3}
                value={descricao}
                onChange={(e) => setDescricao(e.target.value)}
                placeholder="Detalhes do evento"
              />
            </div>
          </div>
          <DialogFooter>
            {modal.editing && (
              <Button variant="destructive" onClick={() => { setConfirmEvento(modal.editing!); closeModal(); }}>
                Excluir
              </Button>
            )}
            <Button variant="outline" onClick={closeModal}>Cancelar</Button>
            <Button onClick={handleSave} disabled={!titulo.trim() || !dataInput || createMut.isPending || patchMut.isPending}>
              Salvar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── detail modal (all types) ── */}
      <Dialog open={detail.open} onOpenChange={(v) => !v && setDetail({ open: false, item: null })}>
        {detail.item && (
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <div className={cn("h-3 w-3 rounded-full flex-shrink-0", TIPO_STYLE[detail.item.tipo].dot)} />
                {detail.item.tipo === "evento" ? "Evento"
                  : detail.item.tipo === "promocao" ? "Promoção"
                  : detail.item.tipo === "conta_pagar" ? "Conta a Pagar"
                  : "Entrega de Insumos"}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium">{detail.item.tipo === "evento" ? "Título" : "Descrição"}: </span>
                {detail.item.label}
              </div>
              {detail.item.tipo === "evento" && detail.item.rawEvento?.descricao && (
                <div><span className="font-medium">Detalhes: </span>{detail.item.rawEvento.descricao}</div>
              )}
              {detail.item.tipo === "promocao" && detail.item.descricao && (
                <div><span className="font-medium">Desconto: </span>{detail.item.descricao}</div>
              )}
              {detail.item.rawCockpit?.fornecedor_nome && (
                <div><span className="font-medium">Fornecedor: </span>{detail.item.rawCockpit.fornecedor_nome}</div>
              )}
              <div>
                <span className="font-medium">Data: </span>
                {new Date(detail.item.dateStr + "T12:00:00").toLocaleDateString("pt-BR")}
              </div>
              {detail.item.horaInicio && (
                <div><span className="font-medium">Horário: </span>{detail.item.horaInicio}–{detail.item.horaFim}</div>
              )}
              {detail.item.rawCockpit?.valor != null && (
                <div>
                  <span className="font-medium">Valor: </span>
                  {Number(detail.item.rawCockpit.valor).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}
                </div>
              )}
            </div>
            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => setDetail({ open: false, item: null })}>Fechar</Button>
              {detail.item.tipo === "evento" && detail.item.rawEvento && (
                <Button onClick={() => {
                  const ev = detail.item!.rawEvento!;
                  setDetail({ open: false, item: null });
                  openEdit(ev);
                }}>
                  Editar
                </Button>
              )}
              {detail.item.tipo === "conta_pagar" && (
                <Button onClick={() => { setDetail({ open: false, item: null }); navigate("/contas-pagar"); }}>
                  Ir ao Financeiro
                </Button>
              )}
              {detail.item.tipo === "entrega_insumo" && (
                <Button onClick={() => { setDetail({ open: false, item: null }); navigate("/compras"); }}>
                  Dar Entrada no Estoque
                </Button>
              )}
            </DialogFooter>
          </DialogContent>
        )}
      </Dialog>
    </div>
  );
}

// ── month view ─────────────────────────────────────────────────────────────

function MonthView({
  year, month, byDate, todayStr, onDayClick, onChipClick, onChipDelete,
}: {
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
          const isCurrentMonth = day.getMonth() === month - 1;
          return (
            <div
              key={ds}
              className={cn(
                "min-h-[90px] border-b border-r p-1 cursor-pointer transition-colors hover:bg-accent/50 last:border-r-0 sm:p-2",
                !isCurrentMonth && "bg-muted/20",
                isToday && "bg-primary/5 ring-1 ring-inset ring-primary/30",
              )}
              onClick={() => onDayClick(ds)}
            >
              <div className={cn(
                "mb-1 flex h-6 w-6 items-center justify-center rounded-full text-xs sm:text-sm",
                isToday ? "bg-primary text-primary-foreground font-semibold" : "text-muted-foreground",
              )}>
                {day.getDate()}
              </div>
              <div className="flex flex-col gap-0.5" onClick={(e) => e.stopPropagation()}>
                {items.slice(0, 3).map((item) => (
                  <Chip
                    key={item.id}
                    item={item}
                    onClick={() => onChipClick(item)}
                    onDelete={item.tipo === "evento" ? () => onChipDelete(item) : undefined}
                  />
                ))}
                {items.length > 3 && (
                  <span className="text-[10px] text-muted-foreground">+{items.length - 3} mais</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

// ── week view ──────────────────────────────────────────────────────────────

function WeekView({
  weekStart, byDate, todayStr, onDayClick, onChipClick, onChipDelete,
}: {
  weekStart: string; byDate: Record<string, CalItem[]>; todayStr: string;
  onDayClick: (ds: string) => void;
  onChipClick: (item: CalItem) => void;
  onChipDelete: (item: CalItem) => void;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      // scroll to 8am (each row ~64px)
      scrollRef.current.scrollTop = 8 * 64;
    }
  }, [weekStart]);

  const weekDays: Date[] = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(weekStart + "T12:00:00");
    d.setDate(d.getDate() + i);
    return d;
  });

  function itemsForDayHour(ds: string, hour: number) {
    return (byDate[ds] ?? []).filter((item) => {
      if (!item.horaInicio) return false; // handled in all-day strip
      return parseInt(item.horaInicio.split(":")[0]) === hour;
    });
  }

  return (
    <Card className="overflow-hidden">
      {/* sticky header */}
      <div className="grid grid-cols-8 border-b bg-background">
        <div className="border-r p-2 text-center text-xs font-medium text-muted-foreground">Hora</div>
        {weekDays.map((day) => {
          const ds = dateToStr(day);
          const isToday = ds === todayStr;
          return (
            <div key={ds} className="border-r p-2 text-center text-xs font-medium last:border-r-0">
              <div className="hidden sm:block text-muted-foreground">
                {day.toLocaleDateString("pt-BR", { weekday: "short" })}
              </div>
              <div className={cn("mx-auto flex h-6 w-6 items-center justify-center rounded-full text-xs",
                isToday ? "bg-primary text-primary-foreground font-semibold" : "text-muted-foreground"
              )}>
                {day.getDate()}
              </div>
            </div>
          );
        })}
      </div>
      {/* all-day strip */}
      <div className="grid grid-cols-8 border-b bg-muted/10">
        <div className="border-r px-1 py-1 text-[10px] text-muted-foreground flex items-center justify-center">
          Dia todo
        </div>
        {weekDays.map((day) => {
          const ds = dateToStr(day);
          const isToday = ds === todayStr;
          const allDayItems = (byDate[ds] ?? []).filter((item) => !item.horaInicio);
          return (
            <div key={ds} className={cn("border-r p-0.5 last:border-r-0 min-h-8 space-y-0.5", isToday && "bg-primary/5")}>
              {allDayItems.map((item) => (
                <Chip key={item.id} item={item} onClick={() => onChipClick(item)}
                  onDelete={item.tipo === "evento" ? () => onChipDelete(item) : undefined} />
              ))}
            </div>
          );
        })}
      </div>
      {/* scrollable body */}
      <div ref={scrollRef} className="overflow-y-auto max-h-[600px]">
        <div className="grid grid-cols-8">
          {HOURS.map((hour) => (
            <>
              <div key={`t-${hour}`} className="border-b border-r p-1 text-[10px] text-muted-foreground sm:p-2 sm:text-xs">
                {String(hour).padStart(2, "0")}:00
              </div>
              {weekDays.map((day) => {
                const ds = dateToStr(day);
                const isToday = ds === todayStr;
                const items = itemsForDayHour(ds, hour);
                return (
                  <div
                    key={`${ds}-${hour}`}
                    className={cn("min-h-12 border-b border-r p-0.5 transition-colors hover:bg-accent/50 last:border-r-0 sm:min-h-16 sm:p-1 cursor-pointer", isToday && "bg-primary/5")}
                    onClick={() => onDayClick(ds)}
                  >
                    <div className="space-y-0.5" onClick={(e) => e.stopPropagation()}>
                      {items.map((item) => (
                        <Chip key={item.id} item={item} onClick={() => onChipClick(item)}
                          onDelete={item.tipo === "evento" ? () => onChipDelete(item) : undefined} />
                      ))}
                    </div>
                  </div>
                );
              })}
            </>
          ))}
        </div>
      </div>
    </Card>
  );
}

// ── day view ───────────────────────────────────────────────────────────────

function DayView({
  dateStr, byDate, onChipClick, onChipDelete,
}: {
  dateStr: string; byDate: Record<string, CalItem[]>;
  onChipClick: (item: CalItem) => void;
  onChipDelete: (item: CalItem) => void;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const items = byDate[dateStr] ?? [];

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 8 * 80;
    }
  }, [dateStr]);

  function itemsForHour(hour: number) {
    return items.filter((item) => {
      if (!item.horaInicio) return hour === 0;
      return parseInt(item.horaInicio.split(":")[0]) === hour;
    });
  }

  return (
    <Card className="overflow-hidden">
      <div ref={scrollRef} className="overflow-y-auto max-h-[600px]">
        <div className="space-y-0">
          {HOURS.map((hour) => {
            const hourItems = itemsForHour(hour);
            return (
              <div key={hour} className="flex border-b last:border-b-0">
                <div className="w-14 flex-shrink-0 border-r p-2 text-xs text-muted-foreground sm:w-20 sm:p-3 sm:text-sm">
                  {String(hour).padStart(2, "0")}:00
                </div>
                <div className="min-h-16 flex-1 p-1 transition-colors hover:bg-accent/50 sm:min-h-20 sm:p-2">
                  <div className="space-y-1">
                    {hourItems.map((item) => (
                      <Chip key={item.id} item={item} onClick={() => onChipClick(item)}
                        onDelete={item.tipo === "evento" ? () => onChipDelete(item) : undefined} />
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}

// ── list view ──────────────────────────────────────────────────────────────

function ListView({
  filtered, todayStr, onChipClick, onChipDelete,
}: {
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
    return (
      <Card className="p-8 text-center text-sm text-muted-foreground">
        Nenhum evento encontrado.
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      <div className="overflow-y-auto max-h-[600px] p-4">
        <div className="space-y-6">
          {Object.entries(grouped).map(([ds, items]) => {
            const label = new Date(ds + "T12:00:00").toLocaleDateString("pt-BR", {
              weekday: "long", day: "numeric", month: "long", year: "numeric",
            });
            const isToday = ds === todayStr;
            return (
              <div key={ds} className="space-y-2">
                <h3 className={cn("text-sm font-semibold capitalize", isToday ? "text-primary" : "text-muted-foreground")}>
                  {label}
                  {isToday && <span className="ml-2 text-xs font-normal">(hoje)</span>}
                </h3>
                <div className="space-y-1.5">
                  {items.map((item) => {
                    const s = TIPO_STYLE[item.tipo];
                    return (
                      <div
                        key={item.id}
                        onClick={() => onChipClick(item)}
                        className="group cursor-pointer rounded-lg border p-3 transition-all hover:shadow-md hover:scale-[1.01]"
                      >
                        <div className="flex items-start gap-3">
                          <div className={cn("mt-1 h-3 w-3 rounded-full flex-shrink-0", s.dot)} />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2">
                              <h4 className="font-medium text-sm group-hover:text-primary transition-colors">{item.label}</h4>
                              <div className="flex items-center gap-1 shrink-0">
                                <Badge variant="secondary" className="text-[10px]">{TIPO_LABEL[item.tipo]}</Badge>
                                {item.tipo === "evento" && (
                                  <button
                                    className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-red-600 transition-opacity"
                                    onClick={(e) => { e.stopPropagation(); onChipDelete(item); }}
                                  >
                                    <X className="h-3.5 w-3.5" />
                                  </button>
                                )}
                              </div>
                            </div>
                            {item.descricao && (
                              <p className="mt-0.5 text-xs text-muted-foreground line-clamp-2">{item.descricao}</p>
                            )}
                            {item.horaInicio && (
                              <div className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                                <Clock className="h-3 w-3" />
                                {item.horaInicio}–{item.horaFim}
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
