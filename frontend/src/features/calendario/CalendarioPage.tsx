import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  useEventos,
  useCreateEvento,
  usePatchEvento,
  useDeleteEvento,
  type EventoResponse,
} from "./useEventos";
import { usePromocoesMes, type PromoçaoResponse } from "@/features/cadastros/promocoes/usePromocoes";
import { useConsolidado, type CockpitItem } from "./useConsolidado";

function getMesLabel(mes: string): string {
  const [year, month] = mes.split("-").map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
}

function getDaysInMonth(year: number, month: number): Date[] {
  const days: Date[] = [];
  const d = new Date(year, month - 1, 1);
  while (d.getMonth() === month - 1) {
    days.push(new Date(d));
    d.setDate(d.getDate() + 1);
  }
  return days;
}

function prevMes(mes: string): string {
  const [y, m] = mes.split("-").map(Number);
  const d = new Date(y, m - 2, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function nextMes(mes: string): string {
  const [y, m] = mes.split("-").map(Number);
  const d = new Date(y, m, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function todayMes(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

const WEEK_DAYS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];

const LAYER_LABELS: Record<string, string> = {
  evento: "Eventos",
  promocao: "Promoções",
  conta_pagar: "Contas a Pagar",
  entrega_insumo: "Entregas",
};

interface ModalState {
  open: boolean;
  dataFixa: string | null;
  editing: EventoResponse | null;
}

interface DetailModal {
  open: boolean;
  item: CockpitItem | null;
}

function isPromoAtiva(p: PromoçaoResponse, date: Date): boolean {
  const d = date.toISOString().slice(0, 10);
  if (d < p.data_inicio) return false;
  if (p.data_fim && d > p.data_fim) return false;
  if (p.recorrencia === "semanal" && p.dias_semana) {
    return p.dias_semana.includes(date.getDay());
  }
  if (p.recorrencia === "mensal" && p.dias_mes) {
    return p.dias_mes.includes(date.getDate());
  }
  return true;
}

export function CalendarioPage() {
  const navigate = useNavigate();
  const [mesAtual, setMesAtual] = useState(todayMes);
  const { data: eventos = [], isLoading } = useEventos(mesAtual);
  const { data: promocoes = [] } = usePromocoesMes(mesAtual);
  const { data: consolidado = [] } = useConsolidado(mesAtual);
  const createMutation = useCreateEvento();
  const patchMutation = usePatchEvento();
  const deleteMutation = useDeleteEvento();

  const [modal, setModal] = useState<ModalState>({ open: false, dataFixa: null, editing: null });
  const [titulo, setTitulo] = useState("");
  const [descricao, setDescricao] = useState("");
  const [dataInput, setDataInput] = useState("");

  const [detailModal, setDetailModal] = useState<DetailModal>({ open: false, item: null });

  // Layer visibility toggles — default all visible
  const allLayers = ["evento", "promocao", "conta_pagar", "entrega_insumo"] as const;
  const [visibleLayers, setVisibleLayers] = useState<Set<string>>(new Set(allLayers));

  // Which tipos are actually present in consolidado (from permission filtering)
  const presentLayers = new Set(consolidado.map((i) => i.tipo));

  function toggleLayer(layer: string) {
    setVisibleLayers((prev) => {
      const next = new Set(prev);
      if (next.has(layer)) next.delete(layer);
      else next.add(layer);
      return next;
    });
  }

  const [year, month] = mesAtual.split("-").map(Number);
  const days = getDaysInMonth(year, month);
  const firstDow = days[0].getDay();

  function openCreate(dataFixa: string | null = null) {
    setModal({ open: true, dataFixa, editing: null });
    setTitulo("");
    setDescricao("");
    setDataInput(dataFixa ?? "");
  }

  function openEdit(ev: EventoResponse) {
    setModal({ open: true, dataFixa: null, editing: ev });
    setTitulo(ev.titulo);
    setDescricao(ev.descricao ?? "");
    setDataInput(ev.data_evento);
  }

  function closeModal() {
    setModal({ open: false, dataFixa: null, editing: null });
  }

  function handleSave() {
    if (!titulo.trim() || !dataInput) return;
    if (modal.editing) {
      patchMutation.mutate(
        { id: modal.editing.id, data: { titulo: titulo.trim(), descricao: descricao || null } },
        { onSuccess: closeModal },
      );
    } else {
      createMutation.mutate(
        { titulo: titulo.trim(), descricao: descricao || null, data_evento: dataInput },
        { onSuccess: closeModal },
      );
    }
  }

  const eventosByDate = eventos.reduce<Record<string, EventoResponse[]>>((acc, ev) => {
    (acc[ev.data_evento] ??= []).push(ev);
    return acc;
  }, {});

  // Group consolidado extras (conta_pagar + entrega_insumo) by date
  const extraByDate = consolidado
    .filter((i) => i.tipo === "conta_pagar" || i.tipo === "entrega_insumo")
    .reduce<Record<string, CockpitItem[]>>((acc, item) => {
      (acc[item.data_referencia] ??= []).push(item);
      return acc;
    }, {});

  const cells: (Date | null)[] = [
    ...Array<null>(firstDow).fill(null),
    ...days,
  ];
  while (cells.length % 7 !== 0) cells.push(null);

  const layerChipClass: Record<string, string> = {
    evento: "bg-blue-100 text-blue-800",
    promocao: "bg-green-100 text-green-800",
    conta_pagar: "bg-red-100 text-red-800",
    entrega_insumo: "bg-yellow-100 text-yellow-800",
  };

  return (
    <div className="p-6 flex flex-col gap-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={() => setMesAtual(prevMes)}>←</Button>
          <h1 className="text-lg font-semibold capitalize">{getMesLabel(mesAtual)}</h1>
          <Button variant="outline" size="sm" onClick={() => setMesAtual(nextMes)}>→</Button>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {allLayers
            .filter((l) => l === "evento" || l === "promocao" || presentLayers.has(l))
            .map((layer) => (
              <label key={layer} className="flex items-center gap-1.5 cursor-pointer text-sm">
                <input
                  type="checkbox"
                  checked={visibleLayers.has(layer)}
                  onChange={() => toggleLayer(layer)}
                  className="accent-blue-600"
                />
                <span
                  className={`rounded px-2 py-0.5 text-xs font-medium ${layerChipClass[layer]}`}
                >
                  {LAYER_LABELS[layer]}
                </span>
              </label>
            ))}
          <Button size="sm" onClick={() => openCreate(null)}>+ Evento</Button>
        </div>
      </div>

      {isLoading ? (
        <div className="h-96 animate-pulse rounded bg-gray-100" />
      ) : (
        <div className="border rounded overflow-hidden">
          <div className="grid grid-cols-7 border-b bg-gray-50">
            {WEEK_DAYS.map((d) => (
              <div key={d} className="py-2 text-center text-xs font-medium text-gray-500">{d}</div>
            ))}
          </div>
          <div className="grid grid-cols-7">
            {cells.map((day, i) => {
              if (!day) {
                return <div key={`empty-${i}`} className="min-h-[90px] border-b border-r bg-gray-50/50" />;
              }
              const dateStr = `${day.getFullYear()}-${String(day.getMonth() + 1).padStart(2, "0")}-${String(day.getDate()).padStart(2, "0")}`;
              const dayEvents = eventosByDate[dateStr] ?? [];
              const dayPromos = promocoes.filter((p) => isPromoAtiva(p, day));
              const dayExtras = extraByDate[dateStr] ?? [];
              const isToday = dateStr === new Date().toISOString().slice(0, 10);
              return (
                <div
                  key={dateStr}
                  className="min-h-[90px] border-b border-r p-1 cursor-pointer hover:bg-blue-50/40 transition-colors"
                  onClick={() => openCreate(dateStr)}
                >
                  <div className={`text-xs font-medium mb-1 w-6 h-6 flex items-center justify-center rounded-full ${isToday ? "bg-blue-600 text-white" : "text-gray-500"}`}>
                    {day.getDate()}
                  </div>
                  <div className="flex flex-col gap-0.5" onClick={(e) => e.stopPropagation()}>
                    {visibleLayers.has("evento") && dayEvents.map((ev) => (
                      <div
                        key={ev.id}
                        className="group flex items-center justify-between rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-800"
                      >
                        <span
                          className="truncate cursor-pointer hover:underline"
                          onClick={() => openEdit(ev)}
                        >
                          {ev.titulo}
                        </span>
                        <button
                          type="button"
                          className="ml-1 shrink-0 opacity-0 group-hover:opacity-100 text-blue-500 hover:text-red-600"
                          onClick={() => deleteMutation.mutate(ev.id)}
                          aria-label="Remover evento"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                    {visibleLayers.has("promocao") && dayPromos.map((p) => (
                      <div
                        key={`promo-${p.id}`}
                        title={`${p.nome} · ${p.tipo_desconto === "porcentagem" ? p.valor_desconto + "%" : "R$ " + p.valor_desconto} · ${p.hora_inicio?.slice(0, 5) ?? "00:00"}–${p.hora_fim?.slice(0, 5) ?? "23:59"}${p.produto_ids.length > 0 ? ` · ${p.produto_ids.length} produto(s)` : ""}`}
                        className="rounded bg-green-100 px-1.5 py-0.5 text-xs text-green-800 truncate cursor-default"
                      >
                        {p.nome}
                      </div>
                    ))}
                    {dayExtras
                      .filter((item) => visibleLayers.has(item.tipo))
                      .map((item) => (
                        <div
                          key={`${item.tipo}-${item.referencia_id}`}
                          className={`rounded px-1.5 py-0.5 text-xs truncate cursor-pointer hover:opacity-80 ${layerChipClass[item.tipo]}`}
                          onClick={() => setDetailModal({ open: true, item })}
                          title={item.descricao}
                        >
                          {item.descricao}
                        </div>
                      ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Evento create/edit modal */}
      <Dialog open={modal.open} onOpenChange={(v) => !v && closeModal()}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>{modal.editing ? "Editar Evento" : "Novo Evento"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-sm text-gray-600">Data</label>
              <Input
                type="date"
                value={dataInput}
                onChange={(e) => setDataInput(e.target.value)}
                disabled={modal.dataFixa !== null}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-600">Título</label>
              <Input
                value={titulo}
                onChange={(e) => setTitulo(e.target.value)}
                placeholder="Nome do evento"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-600">Descrição (opcional)</label>
              <textarea
                className="w-full rounded border px-3 py-2 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
                rows={3}
                value={descricao}
                onChange={(e) => setDescricao(e.target.value)}
                placeholder="Detalhes do evento"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={closeModal}>Cancelar</Button>
            <Button
              onClick={handleSave}
              disabled={!titulo.trim() || !dataInput || createMutation.isPending || patchMutation.isPending}
            >
              Salvar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Detail modal for conta_pagar / entrega_insumo */}
      <Dialog
        open={detailModal.open}
        onOpenChange={(v) => !v && setDetailModal({ open: false, item: null })}
      >
        {detailModal.item && (
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle>
                {detailModal.item.tipo === "conta_pagar" ? "Conta a Pagar" : "Entrega de Insumos"}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium">Fornecedor: </span>
                {detailModal.item.fornecedor_nome ?? detailModal.item.descricao}
              </div>
              <div>
                <span className="font-medium">Data: </span>
                {new Date(detailModal.item.data_referencia + "T12:00:00").toLocaleDateString("pt-BR")}
              </div>
              {detailModal.item.valor != null && (
                <div>
                  <span className="font-medium">Valor: </span>
                  {Number(detailModal.item.valor).toLocaleString("pt-BR", {
                    style: "currency",
                    currency: "BRL",
                  })}
                </div>
              )}
            </div>
            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => setDetailModal({ open: false, item: null })}>
                Fechar
              </Button>
              {detailModal.item.tipo === "conta_pagar" && (
                <Button
                  onClick={() => {
                    setDetailModal({ open: false, item: null });
                    navigate("/contas-pagar");
                  }}
                >
                  Ir para o Financeiro
                </Button>
              )}
              {detailModal.item.tipo === "entrega_insumo" && (
                <Button
                  onClick={() => {
                    setDetailModal({ open: false, item: null });
                    navigate("/compras");
                  }}
                >
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
