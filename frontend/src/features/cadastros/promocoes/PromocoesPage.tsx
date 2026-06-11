import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  usePromocoes,
  useCreatePromocao,
  useUpdatePromocao,
  useDeletePromocao,
  type PromoçaoResponse,
  type PromoçaoCreate,
} from "./usePromocoes";
import { useProdutos } from "@/features/cadastros/produtos/useProdutos";

type Status = "todas" | "ativas" | "futuras";

const DIAS_SEMANA_LABELS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];

function fmtData(d: string | null) {
  if (!d) return "—";
  return new Date(d + "T00:00:00").toLocaleDateString("pt-BR");
}

function fmtDesconto(tipo: string, valor: number) {
  if (tipo === "porcentagem") return `${valor}%`;
  return `R$ ${valor.toFixed(2)}`;
}

interface FormState {
  nome: string;
  descricao: string;
  tipo_desconto: "porcentagem" | "valor_fixo";
  valor_desconto: string;
  data_inicio: string;
  data_fim: string;
  hora_inicio: string;
  hora_fim: string;
  recorrencia: "nenhuma" | "semanal" | "mensal";
  dias_semana: number[];
  dias_mes: number[];
  produto_ids: number[];
}

const EMPTY: FormState = {
  nome: "",
  descricao: "",
  tipo_desconto: "porcentagem",
  valor_desconto: "",
  data_inicio: "",
  data_fim: "",
  hora_inicio: "00:00",
  hora_fim: "23:59",
  recorrencia: "nenhuma",
  dias_semana: [],
  dias_mes: [],
  produto_ids: [],
};

function toForm(p: PromoçaoResponse): FormState {
  return {
    nome: p.nome,
    descricao: p.descricao ?? "",
    tipo_desconto: p.tipo_desconto,
    valor_desconto: String(p.valor_desconto),
    data_inicio: p.data_inicio,
    data_fim: p.data_fim ?? "",
    hora_inicio: p.hora_inicio?.slice(0, 5) ?? "00:00",
    hora_fim: p.hora_fim?.slice(0, 5) ?? "23:59",
    recorrencia: p.recorrencia as FormState["recorrencia"],
    dias_semana: p.dias_semana ?? [],
    dias_mes: p.dias_mes ?? [],
    produto_ids: p.produto_ids,
  };
}

export function PromocoesPage() {
  const [status, setStatus] = useState<Status>("todas");
  const { data: promocoes = [], isLoading } = usePromocoes(status);
  const { data: produtosPage } = useProdutos(undefined, { ativo: true, por_pagina: 500 });
  const produtos = produtosPage?.itens ?? [];
  const createMut = useCreatePromocao();
  const updateMut = useUpdatePromocao();
  const deleteMut = useDeletePromocao();

  const [modal, setModal] = useState<{ open: boolean; editing: PromoçaoResponse | null }>({
    open: false,
    editing: null,
  });
  const [form, setForm] = useState<FormState>(EMPTY);
  const [busca, setBusca] = useState("");

  function openCreate() {
    setForm(EMPTY);
    setModal({ open: true, editing: null });
  }

  function openEdit(p: PromoçaoResponse) {
    setForm(toForm(p));
    setModal({ open: true, editing: p });
  }

  function closeModal() {
    setModal({ open: false, editing: null });
    setBusca("");
  }

  function toggleDiaSemana(d: number) {
    setForm((f) => ({
      ...f,
      dias_semana: f.dias_semana.includes(d)
        ? f.dias_semana.filter((x) => x !== d)
        : [...f.dias_semana, d],
    }));
  }

  function toggleDiaMes(d: number) {
    setForm((f) => ({
      ...f,
      dias_mes: f.dias_mes.includes(d) ? f.dias_mes.filter((x) => x !== d) : [...f.dias_mes, d],
    }));
  }

  function toggleProduto(id: number) {
    setForm((f) => ({
      ...f,
      produto_ids: f.produto_ids.includes(id)
        ? f.produto_ids.filter((x) => x !== id)
        : [...f.produto_ids, id],
    }));
  }

  function handleSave() {
    const payload: PromoçaoCreate = {
      nome: form.nome.trim(),
      descricao: form.descricao || null,
      tipo_desconto: form.tipo_desconto,
      valor_desconto: parseFloat(form.valor_desconto) || 0,
      data_inicio: form.data_inicio,
      data_fim: form.data_fim || null,
      hora_inicio: form.hora_inicio ? form.hora_inicio + ":00" : null,
      hora_fim: form.hora_fim ? form.hora_fim + ":00" : null,
      recorrencia: form.recorrencia,
      dias_semana: form.recorrencia === "semanal" ? form.dias_semana : null,
      dias_mes: form.recorrencia === "mensal" ? form.dias_mes : null,
      produto_ids: form.produto_ids,
    };

    if (modal.editing) {
      updateMut.mutate({ id: modal.editing.id, data: payload }, { onSuccess: closeModal });
    } else {
      createMut.mutate(payload, { onSuccess: closeModal });
    }
  }

  const produtosFiltrados = produtos.filter((p) =>
    p.nome.toLowerCase().includes(busca.toLowerCase())
  );

  const isPending = createMut.isPending || updateMut.isPending;
  const canSave = form.nome.trim() && form.data_inicio && form.valor_desconto;

  const produtosNaMultiplas = (() => {
    if (!modal.open) return new Set<number>();
    const outros = promocoes.filter((p) => !modal.editing || p.id !== modal.editing.id);
    const selected = new Set(form.produto_ids);
    const conflito = new Set<number>();
    for (const p of outros) {
      for (const pid of p.produto_ids) {
        if (selected.has(pid)) conflito.add(pid);
      }
    }
    return conflito;
  })();

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Promoções</h1>
        <Button onClick={openCreate}>+ Promoção</Button>
      </div>

      <div className="mb-3 flex gap-1">
        {(["todas", "ativas", "futuras"] as const).map((s) => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={`rounded border px-3 py-1 text-sm capitalize ${
              status === s ? "bg-gray-900 text-white" : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            {s === "todas" ? "Todas" : s === "ativas" ? "Ativas" : "Futuras"}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />)}
        </div>
      ) : promocoes.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhuma promoção encontrada.</p>
      ) : (
        <div className="rounded border divide-y text-sm">
          {promocoes.map((p) => (
            <div key={p.id} className="flex items-center justify-between px-4 py-3 hover:bg-gray-50">
              <div className="flex flex-col gap-0.5">
                <span className="font-medium">{p.nome}</span>
                <span className="text-xs text-gray-500">
                  {fmtDesconto(p.tipo_desconto, p.valor_desconto)} · {fmtData(p.data_inicio)}
                  {p.data_fim ? ` → ${fmtData(p.data_fim)}` : " (sem fim)"}
                  {p.recorrencia !== "nenhuma" && ` · ${p.recorrencia}`}
                </span>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => openEdit(p)}>
                  Editar
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="text-red-600 hover:text-red-700"
                  onClick={() => deleteMut.mutate(p.id)}
                  disabled={deleteMut.isPending}
                >
                  Remover
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={modal.open} onOpenChange={(v) => !v && closeModal()}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{modal.editing ? "Editar Promoção" : "Nova Promoção"}</DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <label className="mb-1 block text-sm text-gray-600">Nome *</label>
              <Input value={form.nome} onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))} placeholder="Ex: Happy Hour" />
            </div>

            <div>
              <label className="mb-1 block text-sm text-gray-600">Descrição</label>
              <textarea
                className="w-full rounded border px-3 py-2 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
                rows={2}
                value={form.descricao}
                onChange={(e) => setForm((f) => ({ ...f, descricao: e.target.value }))}
                placeholder="Detalhes da promoção"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm text-gray-600">Tipo de Desconto *</label>
                <select
                  className="w-full rounded border px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                  value={form.tipo_desconto}
                  onChange={(e) => setForm((f) => ({ ...f, tipo_desconto: e.target.value as FormState["tipo_desconto"] }))}
                >
                  <option value="porcentagem">Porcentagem (%)</option>
                  <option value="valor_fixo">Valor Fixo (R$)</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm text-gray-600">Valor *</label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={form.valor_desconto}
                  onChange={(e) => setForm((f) => ({ ...f, valor_desconto: e.target.value }))}
                  placeholder={form.tipo_desconto === "porcentagem" ? "Ex: 10" : "Ex: 5.00"}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm text-gray-600">Data Início *</label>
                <Input type="date" value={form.data_inicio} onChange={(e) => setForm((f) => ({ ...f, data_inicio: e.target.value }))} />
              </div>
              <div>
                <label className="mb-1 block text-sm text-gray-600">Data Fim</label>
                <Input type="date" value={form.data_fim} onChange={(e) => setForm((f) => ({ ...f, data_fim: e.target.value }))} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm text-gray-600">Hora Início</label>
                <Input type="time" value={form.hora_inicio} onChange={(e) => setForm((f) => ({ ...f, hora_inicio: e.target.value }))} />
              </div>
              <div>
                <label className="mb-1 block text-sm text-gray-600">Hora Fim</label>
                <Input type="time" value={form.hora_fim} onChange={(e) => setForm((f) => ({ ...f, hora_fim: e.target.value }))} />
              </div>
            </div>

            <div>
              <label className="mb-1 block text-sm text-gray-600">Recorrência</label>
              <select
                className="w-full rounded border px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                value={form.recorrencia}
                onChange={(e) => setForm((f) => ({ ...f, recorrencia: e.target.value as FormState["recorrencia"], dias_semana: [], dias_mes: [] }))}
              >
                <option value="nenhuma">Sem recorrência</option>
                <option value="semanal">Semanal</option>
                <option value="mensal">Mensal</option>
              </select>
            </div>

            {form.recorrencia === "semanal" && (
              <div>
                <label className="mb-1 block text-sm text-gray-600">Dias da Semana *</label>
                <div className="flex gap-1 flex-wrap">
                  {DIAS_SEMANA_LABELS.map((label, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => toggleDiaSemana(i)}
                      className={`rounded border px-2 py-1 text-xs ${
                        form.dias_semana.includes(i)
                          ? "bg-blue-600 text-white border-blue-600"
                          : "bg-white text-gray-600 hover:bg-gray-50"
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {form.recorrencia === "mensal" && (
              <div>
                <label className="mb-1 block text-sm text-gray-600">Dias do Mês *</label>
                <div className="flex gap-1 flex-wrap">
                  {Array.from({ length: 31 }, (_, i) => i + 1).map((d) => (
                    <button
                      key={d}
                      type="button"
                      onClick={() => toggleDiaMes(d)}
                      className={`rounded border w-8 h-7 text-xs ${
                        form.dias_mes.includes(d)
                          ? "bg-blue-600 text-white border-blue-600"
                          : "bg-white text-gray-600 hover:bg-gray-50"
                      }`}
                    >
                      {d}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div>
              <label className="mb-1 block text-sm text-gray-600">
                Produtos ({form.produto_ids.length} selecionado{form.produto_ids.length !== 1 ? "s" : ""})
              </label>
              <Input
                placeholder="Buscar produto..."
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                className="mb-2"
              />
              <div className="max-h-36 overflow-y-auto rounded border divide-y text-sm">
                {produtosFiltrados.length === 0 ? (
                  <p className="px-3 py-2 text-gray-400 text-xs">Nenhum produto encontrado.</p>
                ) : (
                  produtosFiltrados.map((p) => (
                    <label key={p.id} className="flex items-center gap-2 px-3 py-1.5 cursor-pointer hover:bg-gray-50">
                      <input
                        type="checkbox"
                        checked={form.produto_ids.includes(p.id)}
                        onChange={() => toggleProduto(p.id)}
                      />
                      <span>{p.nome}</span>
                    </label>
                  ))
                )}
              </div>
            </div>

            {produtosNaMultiplas.size > 0 && (
              <div className="rounded bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-800">
                Produto(s) selecionado(s) já constam em outra promoção ativa. Em conflito, aplica a promoção mais antiga (menor ID).
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={closeModal}>Cancelar</Button>
            <Button onClick={handleSave} disabled={!canSave || isPending}>
              Salvar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
