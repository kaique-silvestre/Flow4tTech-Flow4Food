import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useGarcons } from "@/features/cadastros/garcons/useGarcons";
import { useProdutos } from "@/features/cadastros/produtos/useProdutos";
import { formatCurrency, formatQuantidade } from "@/lib/format";
import { CancelarItemModal } from "./CancelarItemModal";
import { useComanda, useEditarItem, useLancarItem, usePatchComanda, useReopenComanda, useTopItens, type ItemComandaResponse } from "./useComandas";

export function ComandaAbertaPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const comanda_id = Number(id);

  const { data: comanda, isLoading, isError } = useComanda(comanda_id);
  const lancarItem = useLancarItem(comanda_id);
  const editarItem = useEditarItem(comanda_id);
  const patchComanda = usePatchComanda(comanda_id);
  const { data: topItens = [] } = useTopItens(7, 6);
  const { data: garcons = [] } = useGarcons();

  const [editingField, setEditingField] = useState<"identificacao" | "garcom" | null>(null);
  const [editIdentificacao, setEditIdentificacao] = useState("");
  const [editGarcomId, setEditGarcomId] = useState<number>(0);

  function startEditIdentificacao() {
    setEditIdentificacao(comanda?.identificacao ?? "");
    setEditingField("identificacao");
  }

  function startEditGarcom() {
    setEditGarcomId(comanda?.garcom_id ?? 0);
    setEditingField("garcom");
  }

  function saveIdentificacao() {
    if (!editIdentificacao.trim()) { setEditingField(null); return; }
    patchComanda.mutate(
      { identificacao: editIdentificacao.trim() },
      { onSuccess: () => setEditingField(null) },
    );
  }

  function saveGarcom() {
    if (!editGarcomId) { setEditingField(null); return; }
    patchComanda.mutate(
      { garcom_id: editGarcomId },
      { onSuccess: () => setEditingField(null) },
    );
  }

  const [busca, setBusca] = useState("");
  const { data: itens = [] } = useProdutos(busca || undefined);

  const [itemSelecionado, setItemSelecionado] = useState<number | null>(null);
  const [quantidade, setQuantidade] = useState("1");
  const [pessoaAssociada, setPessoaAssociada] = useState("");
  const [observacao, setObservacao] = useState("");
  const [cortesia, setCortesia] = useState(false);

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editQtd, setEditQtd] = useState("");
  const [editPessoa, setEditPessoa] = useState("");
  const [editObs, setEditObs] = useState("");

  const [cancelando, setCancelando] = useState<ItemComandaResponse | null>(null);
  const [confirmReabrir, setConfirmReabrir] = useState(false);

  const reopenComanda = useReopenComanda(comanda_id);

  const itemSelecionadoObj = itemSelecionado != null
    ? (itens.find((i) => i.id === itemSelecionado) ?? topItens.find((i) => i.id === itemSelecionado))
    : null;

  function handleLancar() {
    if (!comanda || itemSelecionado == null) return;
    lancarItem.mutate(
      {
        item_id: itemSelecionado,
        quantidade: Number(quantidade),
        pessoa_associada: pessoaAssociada || undefined,
        observacao: observacao || undefined,
        cortesia,
        version: comanda.version,
      },
      {
        onSuccess: () => {
          setItemSelecionado(null);
          setQuantidade("1");
          setPessoaAssociada("");
          setObservacao("");
          setCortesia(false);
          setBusca("");
        },
      },
    );
  }

  function startEdit(ic: ItemComandaResponse) {
    setEditingId(ic.id);
    setEditQtd(String(ic.quantidade));
    setEditPessoa(ic.pessoa_associada ?? "");
    setEditObs(ic.observacao ?? "");
  }

  function saveEdit(ic: ItemComandaResponse) {
    if (!comanda) return;
    editarItem.mutate(
      {
        item_id: ic.id,
        version: comanda.version,
        quantidade: Number(editQtd),
        pessoa_associada: editPessoa || undefined,
        observacao: editObs || undefined,
      },
      { onSuccess: () => setEditingId(null) },
    );
  }

  if (isError) {
    return (
      <div className="p-6">
        <Button variant="outline" size="sm" onClick={() => navigate("/comandas")} className="mb-4">
          ← Voltar
        </Button>
        <p className="text-sm text-red-500">Comanda não encontrada ou erro ao carregar. Verifique se ela ainda existe.</p>
      </div>
    );
  }

  if (isLoading || !comanda) {
    return (
      <div className="p-6 space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
        ))}
      </div>
    );
  }

  if (comanda.status === "fechada") {
    const itensNaoCancelados = comanda.itens_ativos.filter((i) => !i.cancelado);
    return (
      <div className="p-6 max-w-2xl">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold">
              #{comanda.id} — {comanda.tipo_identificacao === "mesa" ? "Mesa" : ""} {comanda.identificacao}
            </h1>
            <p className="text-sm text-gray-500">Garçom: {comanda.garcom_nome}</p>
          </div>
          <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600">
            fechada
          </span>
        </div>

        <div className="rounded border bg-white p-4 space-y-2 mb-4">
          {itensNaoCancelados.map((ic) => (
            <div key={ic.id} className="flex justify-between text-sm">
              <span>{formatQuantidade(ic.quantidade)} × {ic.item_nome}{ic.cortesia ? " (cortesia)" : ""}</span>
              <span>{formatCurrency(Number(ic.subtotal))}</span>
            </div>
          ))}
          <div className="border-t pt-2 flex justify-between font-semibold">
            <span>Total</span>
            <span>{comanda.total != null ? formatCurrency(Number(comanda.total)) : "—"}</span>
          </div>
        </div>

        <div className="flex gap-3">
          <Button variant="outline" onClick={() => navigate(`/comprovante/${comanda_id}`)}>
            Ver Comprovante
          </Button>
          <Button onClick={() => setConfirmReabrir(true)}>
            Reabrir Comanda
          </Button>
        </div>

        <ConfirmDialog
          open={confirmReabrir}
          title="Reabrir comanda?"
          description="Os pagamentos serão estornados e o estoque restaurado."
          confirmLabel="Reabrir"
          onConfirm={() => reopenComanda.mutate()}
          onCancel={() => setConfirmReabrir(false)}
          isPending={reopenComanda.isPending}
        />
      </div>
    );
  }

  const isEditable = comanda.status === "aberta" || comanda.status === "reaberta";
  const itensAtivos = comanda.itens_ativos.filter((i) => !i.cancelado);
  const itensCancelados = comanda.itens_ativos.filter((i) => i.cancelado);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Header */}
      <div className="border-b bg-white px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm" onClick={() => navigate("/comandas")}>
              ← Voltar
            </Button>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-lg font-semibold">#{comanda.id} —</span>
                {editingField === "identificacao" ? (
                  <Input
                    autoFocus
                    className="h-7 w-40 text-base font-semibold"
                    value={editIdentificacao}
                    onChange={(e) => setEditIdentificacao(e.target.value)}
                    onBlur={saveIdentificacao}
                    onKeyDown={(e) => { if (e.key === "Enter") saveIdentificacao(); if (e.key === "Escape") setEditingField(null); }}
                  />
                ) : (
                  <span className="text-lg font-semibold">
                    {comanda.tipo_identificacao === "mesa" ? "Mesa " : ""}{comanda.identificacao}
                  </span>
                )}
                {isEditable && (
                  <button
                    type="button"
                    className="text-gray-400 hover:text-gray-600 text-sm"
                    onClick={startEditIdentificacao}
                    title="Editar identificação"
                  >
                    ✏
                  </button>
                )}
              </div>
              <div className="flex items-center gap-1 text-sm text-gray-500">
                <span>Garçom:</span>
                {editingField === "garcom" ? (
                  <select
                    autoFocus
                    className="rounded border px-1 py-0.5 text-sm"
                    value={editGarcomId}
                    onChange={(e) => setEditGarcomId(Number(e.target.value))}
                    onBlur={saveGarcom}
                    onKeyDown={(e) => { if (e.key === "Enter") saveGarcom(); if (e.key === "Escape") setEditingField(null); }}
                  >
                    <option value={0}>Selecione...</option>
                    {garcons.filter((g) => g.ativo).map((g) => (
                      <option key={g.id} value={g.id}>{g.nome}</option>
                    ))}
                  </select>
                ) : (
                  <span>{comanda.garcom_nome}</span>
                )}
                {isEditable && (
                  <button
                    type="button"
                    className="text-gray-400 hover:text-gray-600 text-xs ml-0.5"
                    onClick={startEditGarcom}
                    title="Editar garçom"
                  >
                    ✏
                  </button>
                )}
                <span>· Aberta há {comanda.tempo_aberta_minutos} min</span>
              </div>
            </div>
          </div>
          <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">
            {comanda.status}
          </span>
        </div>
        {comanda.pessoas.length > 0 && (
          <div className="mt-1 flex gap-2">
            {comanda.pessoas.map((p, i) => (
              <span key={i} className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                {p}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Split layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel — lançar item */}
        <div className="flex w-80 flex-col gap-4 overflow-y-auto border-r bg-gray-50 p-4">
          <h3 className="font-medium">Adicionar Item</h3>

          {/* Busca */}
          <Input
            placeholder="Buscar item..."
            value={busca}
            onChange={(e) => { setBusca(e.target.value); setItemSelecionado(null); }}
          />

          {/* Top atalhos */}
          {!busca && topItens.length > 0 && (
            <div>
              <p className="mb-1 text-xs text-gray-400">Mais pedidos</p>
              <div className="grid grid-cols-2 gap-1">
                {topItens.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setItemSelecionado(item.id)}
                    className={`rounded border p-2 text-left text-xs transition-colors ${
                      itemSelecionado === item.id
                        ? "border-blue-400 bg-blue-50"
                        : "border-gray-200 bg-white hover:bg-gray-50"
                    }`}
                  >
                    <div className="font-medium">{item.nome}</div>
                    <div className="text-gray-400">
                      {item.preco_venda != null ? formatCurrency(item.preco_venda) : "—"}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Resultados busca */}
          {busca && (
            <div className="max-h-48 space-y-1 overflow-y-auto">
              {itens.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setItemSelecionado(item.id)}
                  className={`w-full rounded border p-2 text-left text-sm transition-colors ${
                    itemSelecionado === item.id
                      ? "border-blue-400 bg-blue-50"
                      : "border-gray-200 bg-white hover:bg-gray-50"
                  }`}
                >
                  {item.nome}
                  {item.preco_venda != null && (
                    <span className="ml-2 text-gray-400">{formatCurrency(item.preco_venda)}</span>
                  )}
                </button>
              ))}
              {itens.length === 0 && (
                <p className="text-xs text-gray-400">Nenhum item encontrado</p>
              )}
            </div>
          )}

          {/* Detalhes do item selecionado */}
          {itemSelecionadoObj && (
            <div className="rounded border bg-blue-50 p-3 text-sm">
              <div className="font-medium">{itemSelecionadoObj.nome}</div>
              {itemSelecionadoObj.preco_venda != null && (
                <div className="text-gray-500">{formatCurrency(itemSelecionadoObj.preco_venda)}</div>
              )}
            </div>
          )}

          {/* Quantidade */}
          <div>
            <Label htmlFor="qtd">Quantidade</Label>
            <Input
              id="qtd"
              type="number"
              min="0.001"
              step="0.001"
              value={quantidade}
              onChange={(e) => setQuantidade(e.target.value)}
              className="mt-1"
            />
          </div>

          {/* Pessoa */}
          {comanda.pessoas.length > 0 ? (
            <div>
              <Label>Pessoa</Label>
              <select
                className="mt-1 w-full rounded border px-3 py-2 text-sm"
                value={pessoaAssociada}
                onChange={(e) => setPessoaAssociada(e.target.value)}
              >
                <option value="">— nenhuma —</option>
                {comanda.pessoas.map((p, i) => (
                  <option key={i} value={p}>{p}</option>
                ))}
              </select>
            </div>
          ) : (
            <div>
              <Label htmlFor="pessoa">Pessoa (opcional)</Label>
              <Input
                id="pessoa"
                value={pessoaAssociada}
                onChange={(e) => setPessoaAssociada(e.target.value)}
                className="mt-1"
              />
            </div>
          )}

          {/* Observação */}
          <div>
            <Label htmlFor="obs">Observação (opcional)</Label>
            <Input
              id="obs"
              value={observacao}
              onChange={(e) => setObservacao(e.target.value)}
              className="mt-1"
            />
          </div>

          {/* Cortesia */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="cortesia"
              checked={cortesia}
              onChange={(e) => setCortesia(e.target.checked)}
            />
            <Label htmlFor="cortesia">Cortesia (preço zero)</Label>
          </div>

          <Button
            onClick={handleLancar}
            disabled={!itemSelecionado || lancarItem.isPending}
          >
            {lancarItem.isPending ? "Lançando..." : "+ Adicionar Item"}
          </Button>
        </div>

        {/* Right panel — itens lançados */}
        <div className="flex flex-1 flex-col overflow-y-auto p-4">
          <h3 className="mb-3 font-medium">
            Itens Lançados ({itensAtivos.length})
          </h3>

          {itensAtivos.length === 0 ? (
            <p className="text-sm text-gray-400">Nenhum item lançado ainda.</p>
          ) : (
            <div className="space-y-2">
              {itensAtivos.map((ic) => (
                <div key={ic.id} className="rounded border bg-white p-3">
                  {editingId === ic.id ? (
                    <div className="space-y-2">
                      <div className="flex gap-2">
                        <Input
                          type="number"
                          value={editQtd}
                          onChange={(e) => setEditQtd(e.target.value)}
                          className="w-24"
                        />
                        <Input
                          value={editPessoa}
                          onChange={(e) => setEditPessoa(e.target.value)}
                          placeholder="Pessoa"
                        />
                        <Input
                          value={editObs}
                          onChange={(e) => setEditObs(e.target.value)}
                          placeholder="Obs"
                        />
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" onClick={() => saveEdit(ic)} disabled={editarItem.isPending}>
                          Salvar
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setEditingId(null)}>
                          Cancelar
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2 font-medium">
                          {formatQuantidade(ic.quantidade)} × {ic.item_nome}
                          {ic.cortesia && (
                            <span className="rounded-full bg-purple-100 px-2 py-0.5 text-xs text-purple-600">
                              cortesia
                            </span>
                          )}
                        </div>
                        {ic.pessoa_associada && (
                          <div className="text-xs text-gray-400">{ic.pessoa_associada}</div>
                        )}
                        {ic.observacao && (
                          <div className="text-xs text-gray-400">Obs: {ic.observacao}</div>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-right">
                        <div className="text-sm font-medium">
                          {formatCurrency(Number(ic.subtotal))}
                        </div>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => startEdit(ic)}
                        >
                          Editar
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => setCancelando(ic)}
                        >
                          ✕
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Cancelados */}
          {itensCancelados.length > 0 && (
            <div className="mt-4">
              <p className="mb-1 text-xs text-gray-400">Itens cancelados</p>
              {itensCancelados.map((ic) => (
                <div key={ic.id} className="rounded border border-dashed p-2 text-sm text-gray-400 line-through">
                  {formatQuantidade(ic.quantidade)} × {ic.item_nome}
                </div>
              ))}
            </div>
          )}

          {/* Rodapé total */}
          <div className="mt-auto border-t pt-3 flex items-center justify-between">
            <Button
              variant="default"
              onClick={() => navigate(`/comandas/${id}/fechar`)}
            >
              Fechar Conta
            </Button>
            <div className="text-right">
              <span className="text-sm text-gray-500">Total parcial: </span>
              <span className="text-lg font-semibold">
                {formatCurrency(Number(comanda.total_parcial))}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Modal cancelar */}
      {cancelando && comanda && (
        <CancelarItemModal
          comanda_id={comanda.id}
          item_id={cancelando.id}
          version={comanda.version}
          onClose={() => setCancelando(null)}
          onSuccess={() => setCancelando(null)}
        />
      )}
    </div>
  );
}
