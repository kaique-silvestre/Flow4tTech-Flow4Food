import { useState, useEffect, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useGarcons } from "@/features/cadastros/garcons/useGarcons";
import { useProdutos } from "@/features/cadastros/produtos/useProdutos";
import { useCategorias, flattenCategorias } from "@/features/cadastros/categorias/useCategorias";
import { formatCurrency, formatQuantidade } from "@/lib/format";
import { CancelarItemModal } from "./CancelarItemModal";
import { useComanda, useCancelarComanda, useEditarItem, useLancarItem, usePatchComanda, useReopenComanda, type ItemComandaResponse } from "./useComandas";

export function ComandaAbertaPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const comanda_id = Number(id);

  const { data: comanda, isLoading, isError } = useComanda(comanda_id);
  const lancarItem = useLancarItem(comanda_id);
  const editarItem = useEditarItem(comanda_id);
  const patchComanda = usePatchComanda(comanda_id);
  const { data: garconsData } = useGarcons();
  const garcons = garconsData?.itens ?? [];

  const [editingField, setEditingField] = useState<"identificacao" | "garcom" | null>(null);
  const [editIdentificacao, setEditIdentificacao] = useState("");
  const [editGarcomId, setEditGarcomId] = useState<number>(0);
  const [novaPessoa, setNovaPessoa] = useState("");

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
  const { data: produtosPage } = useProdutos(undefined, { ativo: true });
  const todosProdutos = useMemo(() => produtosPage?.itens ?? [], [produtosPage]);
  const { data: categoriasTree = [] } = useCategorias();
  const categoriaFlat = useMemo(() => flattenCategorias(categoriasTree), [categoriasTree]);
  const categoriaMap = useMemo(() =>
    Object.fromEntries(categoriaFlat.map((c) => [c.id, c.nome])),
    [categoriaFlat]
  );

  const itens = useMemo(() => {
    if (!busca.trim()) return todosProdutos;
    const q = busca.toLowerCase();
    return todosProdutos.filter((p) => p.nome.toLowerCase().includes(q));
  }, [todosProdutos, busca]);

  const itensPorCategoria = useMemo(() => {
    const grupos: { label: string; produtos: typeof todosProdutos }[] = [];
    const mapa = new Map<string, typeof todosProdutos>();
    for (const p of itens) {
      const label = p.categoria_id != null ? (categoriaMap[p.categoria_id] ?? "Sem categoria") : "Sem categoria";
      if (!mapa.has(label)) mapa.set(label, []);
      mapa.get(label)!.push(p);
    }
    for (const [label, produtos] of mapa) {
      grupos.push({ label, produtos });
    }
    return grupos;
  }, [itens, categoriaMap]);

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
  const [confirmCancelar, setConfirmCancelar] = useState(false);
  const [mobileTab, setMobileTab] = useState<"cardapio" | "itens">("cardapio");

  const reopenComanda = useReopenComanda(comanda_id);
  const cancelarComanda = useCancelarComanda(comanda_id, comanda?.version ?? 0);

  const [now, setNow] = useState(() => Date.now());
  const comandaStatus = comanda?.status;
  useEffect(() => {
    if (!comandaStatus || comandaStatus === "fechada") return;
    const id = setInterval(() => setNow(Date.now()), 1_000);
    return () => clearInterval(id);
  }, [comandaStatus]);

  function parseUtc(iso: string): number {
    const s = iso.endsWith("Z") || iso.includes("+") ? iso : iso + "Z";
    return new Date(s).getTime();
  }

  function formatTempo(iso: string): string {
    const ms = now - parseUtc(iso);
    const totalMin = Math.floor(ms / 60_000);
    if (totalMin < 60) return `${totalMin} min`;
    const h = Math.floor(totalMin / 60);
    const m = totalMin % 60;
    return `${h}h ${m}min`;
  }

  const itemSelecionadoObj = itemSelecionado != null
    ? todosProdutos.find((i) => i.id === itemSelecionado) ?? null
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

  function handleImprimir() {
    navigate(`/vendas/comandas/${id}/pre-conta`);
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
        <Button variant="outline" size="sm" onClick={() => navigate("/vendas/comandas")} className="mb-4">
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
              {comanda.numero_dia != null ? `#${comanda.numero_dia}` : `#${comanda.id}`} — {comanda.tipo_identificacao === "mesa" ? "Mesa" : ""} {comanda.identificacao}
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

  function renderItensLista() {
    return (
      <>
        {itensAtivos.length === 0 ? (
          <p className="text-sm text-gray-400">Nenhum item lançado ainda.</p>
        ) : (
          <div className="space-y-2">
            {itensAtivos.map((ic) => (
              <div key={ic.id} className="rounded border bg-white p-3">
                {editingId === ic.id ? (
                  <div className="space-y-2">
                    <div className="flex flex-wrap gap-2">
                      <Input
                        type="number"
                        value={editQtd}
                        onChange={(e) => setEditQtd(e.target.value)}
                        className="w-24"
                      />
                      {(comanda?.pessoas.length ?? 0) > 0 ? (
                        <select
                          className="rounded border px-2 py-1.5 text-sm"
                          value={editPessoa}
                          onChange={(e) => setEditPessoa(e.target.value)}
                        >
                          <option value="">— nenhuma —</option>
                          {comanda?.pessoas.map((p, i) => (
                            <option key={i} value={p}>{p}</option>
                          ))}
                        </select>
                      ) : (
                        <Input
                          value={editPessoa}
                          onChange={(e) => setEditPessoa(e.target.value)}
                          placeholder="Pessoa"
                        />
                      )}
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
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex flex-wrap items-center gap-2 font-medium">
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
                    <div className="flex shrink-0 items-center gap-2 text-right">
                      <div className="text-sm font-medium">
                        {formatCurrency(Number(ic.subtotal))}
                      </div>
                      <Button size="sm" variant="outline" onClick={() => startEdit(ic)}>
                        Editar
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => setCancelando(ic)}>
                        ✕
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

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
      </>
    );
  }

  return (
    /* pb-16 on mobile reserves space for the fixed bottom bar */
    <div className="flex h-full flex-col overflow-hidden pb-16 lg:pb-0">
      {/* Header */}
      <div className="border-b bg-white px-4 py-3 lg:px-6">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm" onClick={() => navigate("/vendas/comandas")}>
              ← Voltar
            </Button>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-lg font-semibold">{comanda.numero_dia != null ? `#${comanda.numero_dia}` : `#${comanda.id}`} —</span>
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
                    className="min-h-[44px] min-w-[44px] text-gray-400 hover:text-gray-600 text-sm"
                    onClick={startEditIdentificacao}
                    title="Editar identificação"
                  >
                    ✏
                  </button>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-1 text-sm text-gray-500">
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
                    className="min-h-[44px] min-w-[44px] text-gray-400 hover:text-gray-600 text-xs"
                    onClick={startEditGarcom}
                    title="Editar garçom"
                  >
                    ✏
                  </button>
                )}
                <span>· Aberta há {formatTempo(comanda.created_at)}</span>
              </div>
            </div>
          </div>
          <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">
            {comanda.status}
          </span>
        </div>
        {isEditable && (
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {comanda.pessoas.map((p, i) => (
              <span key={i} className="flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                {p}
                {comanda.pessoas.length > 1 && (
                  <button
                    type="button"
                    className="text-gray-400 hover:text-gray-700"
                    onClick={() => {
                      const novaLista = comanda.pessoas.filter((_, j) => j !== i);
                      patchComanda.mutate({ pessoas: novaLista });
                    }}
                  >
                    ×
                  </button>
                )}
              </span>
            ))}
            <div className="flex items-center gap-1">
              <input
                className="h-6 rounded border px-2 text-xs w-28"
                placeholder="+ pessoa"
                value={novaPessoa}
                onChange={(e) => setNovaPessoa(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    const nome = novaPessoa.trim();
                    if (!nome || comanda.pessoas.includes(nome)) return;
                    patchComanda.mutate({ pessoas: [...comanda.pessoas, nome] });
                    setNovaPessoa("");
                  }
                }}
              />
              <button
                type="button"
                className="text-xs text-blue-600 hover:underline"
                onClick={() => {
                  const nome = novaPessoa.trim();
                  if (!nome || comanda.pessoas.includes(nome)) return;
                  patchComanda.mutate({ pessoas: [...comanda.pessoas, nome] });
                  setNovaPessoa("");
                }}
              >
                Add
              </button>
            </div>
          </div>
        )}
        {!isEditable && comanda.pessoas.length > 0 && (
          <div className="mt-1 flex gap-2">
            {comanda.pessoas.map((p, i) => (
              <span key={i} className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                {p}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Mobile tabs */}
      <div className="flex border-b bg-white lg:hidden">
        <button
          className={`flex-1 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            mobileTab === "cardapio"
              ? "border-blue-500 text-blue-600"
              : "border-transparent text-gray-500"
          }`}
          onClick={() => setMobileTab("cardapio")}
        >
          Cardápio
        </button>
        <button
          className={`flex-1 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            mobileTab === "itens"
              ? "border-blue-500 text-blue-600"
              : "border-transparent text-gray-500"
          }`}
          onClick={() => setMobileTab("itens")}
        >
          Itens ({itensAtivos.length})
        </button>
      </div>

      {/* Split layout: col on mobile, row on desktop */}
      <div className="flex flex-1 flex-col overflow-hidden lg:flex-row">
        {/* Left panel — catálogo persistente + form fixo embaixo */}
        <div className={`flex-col overflow-hidden border-b bg-gray-50 lg:w-80 lg:flex-none lg:border-b-0 lg:border-r ${mobileTab === "cardapio" ? "flex" : "hidden lg:flex"}`}>
          {/* Metade superior: busca + catálogo */}
          <div className="flex flex-1 flex-col overflow-hidden border-b">
            <div className="p-3 bg-white shrink-0">
              <Input
                placeholder="Buscar produto..."
                value={busca}
                onChange={(e) => {
                  setBusca(e.target.value);
                  setItemSelecionado(null);
                }}
                onKeyDown={(e) => { if (e.key === "Escape") setBusca(""); }}
              />
            </div>
          <div className="flex-1 overflow-y-auto p-3">
            {itensPorCategoria.length === 0 ? (
              <p className="text-xs text-gray-400 py-2">Nenhum produto encontrado</p>
            ) : (
              itensPorCategoria.map(({ label, produtos }) => (
                <div key={label} className="mb-3">
                  <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-gray-400">{label}</p>
                  <div className="grid grid-cols-2 gap-1.5">
                    {produtos.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => setItemSelecionado(item.id === itemSelecionado ? null : item.id)}
                        className={`min-h-[52px] rounded-lg border p-2 text-left text-xs transition-colors ${
                          itemSelecionado === item.id
                            ? "border-blue-400 bg-blue-50 ring-1 ring-blue-300"
                            : "border-gray-200 bg-white hover:bg-gray-50 hover:border-gray-300"
                        }`}
                      >
                        <div className="font-medium leading-tight text-gray-800">{item.nome}</div>
                        <div className="mt-0.5 text-gray-400">
                          {item.preco_venda != null ? formatCurrency(item.preco_venda) : "—"}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>

          </div>{/* fecha metade superior */}

          {/* Metade inferior: form */}
          <div className="flex flex-1 flex-col overflow-y-auto bg-white p-3 space-y-2.5">
            {itemSelecionadoObj ? (
              <div className="rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-sm flex items-center justify-between">
                <span className="font-medium text-blue-800">{itemSelecionadoObj.nome}</span>
                {itemSelecionadoObj.preco_venda != null && (
                  <span className="text-blue-600 text-xs">{formatCurrency(itemSelecionadoObj.preco_venda)}</span>
                )}
              </div>
            ) : (
              <p className="text-xs text-gray-400 text-center py-1">Selecione um produto acima</p>
            )}

            <div className="flex gap-2">
              <div className="flex-1">
                <Label htmlFor="qtd" className="text-xs">Qtd</Label>
                <Input
                  id="qtd"
                  type="number"
                  min="0.001"
                  step="0.001"
                  value={quantidade}
                  onChange={(e) => setQuantidade(e.target.value)}
                  className="mt-0.5"
                />
              </div>
              {comanda.pessoas.length > 0 ? (
                <div className="flex-1">
                  <Label className="text-xs">Pessoa</Label>
                  <select
                    className="mt-0.5 w-full rounded border px-2 py-2 text-sm"
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
                <div className="flex-1">
                  <Label htmlFor="pessoa" className="text-xs">Pessoa</Label>
                  <Input
                    id="pessoa"
                    value={pessoaAssociada}
                    onChange={(e) => setPessoaAssociada(e.target.value)}
                    className="mt-0.5"
                    placeholder="Opcional"
                  />
                </div>
              )}
            </div>

            <div>
              <Label htmlFor="obs" className="text-xs">Observação</Label>
              <Input
                id="obs"
                value={observacao}
                onChange={(e) => setObservacao(e.target.value)}
                className="mt-0.5"
                placeholder="Opcional"
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="cortesia"
                  checked={cortesia}
                  onChange={(e) => setCortesia(e.target.checked)}
                />
                <Label htmlFor="cortesia" className="text-xs">Cortesia</Label>
              </div>
              <Button
                onClick={handleLancar}
                disabled={!itemSelecionado || lancarItem.isPending}
                size="sm"
              >
                {lancarItem.isPending ? "Lançando..." : "+ Adicionar"}
              </Button>
            </div>
          </div>
        </div>

        {/* Right panel — itens lançados */}
        <div className={`flex-1 flex-col overflow-hidden ${mobileTab === "itens" ? "flex" : "hidden lg:flex"}`}>
          <div className="flex-1 overflow-y-auto p-4">
            <h3 className="mb-3 font-medium">
              Itens Lançados ({itensAtivos.length})
            </h3>
            {renderItensLista()}
          </div>

          <div className="flex items-center justify-between border-t bg-white px-4 py-3">
            <div className="flex gap-2">
              <Button
                variant="default"
                onClick={() => navigate(`/vendas/comandas/${id}/fechar`)}
                disabled={itensAtivos.length === 0}
                title={itensAtivos.length === 0 ? "Adicione ao menos um item antes de fechar" : undefined}
              >
                Fechar Conta
              </Button>
              <Button variant="outline" onClick={handleImprimir}>
                Imprimir Conta
              </Button>
              <Button variant="destructive" onClick={() => setConfirmCancelar(true)}>
                Cancelar Comanda
              </Button>
            </div>
            <div className="text-right">
              <span className="text-sm text-gray-500">Total parcial: </span>
              <span className="text-lg font-semibold">
                {formatCurrency(Number(comanda.total_parcial))}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile fixed bottom bar */}
      <div className="fixed inset-x-0 bottom-0 z-30 flex items-center justify-between border-t bg-white px-4 py-3 lg:hidden">
        <div>
          <p className="text-xs text-gray-500">{itensAtivos.length} {itensAtivos.length === 1 ? "item" : "itens"}</p>
          <p className="font-semibold">{formatCurrency(Number(comanda.total_parcial))}</p>
        </div>
        {mobileTab === "itens" ? (
          <div className="flex gap-2">
            <Button
              variant="default"
              onClick={() => navigate(`/vendas/comandas/${id}/fechar`)}
              disabled={itensAtivos.length === 0}
            >
              Fechar Conta
            </Button>
            <Button variant="outline" onClick={handleImprimir}>
              Imprimir
            </Button>
            <Button variant="destructive" onClick={() => setConfirmCancelar(true)}>
              Cancelar
            </Button>
          </div>
        ) : (
          <Button onClick={() => setMobileTab("itens")}>
            Ver Itens
          </Button>
        )}
      </div>

      <CancelarItemModal
        open={!!cancelando && !!comanda}
        comanda_id={comanda?.id ?? 0}
        item_id={cancelando?.id ?? 0}
        version={comanda?.version ?? 0}
        onClose={() => setCancelando(null)}
        onSuccess={() => setCancelando(null)}
      />

      <ConfirmDialog
        open={confirmCancelar}
        title="Cancelar comanda?"
        description="A comanda será cancelada e o estoque reservado será liberado. Esta ação não pode ser desfeita."
        confirmLabel="Cancelar Comanda"
        onConfirm={() => cancelarComanda.mutate()}
        onCancel={() => setConfirmCancelar(false)}
        isPending={cancelarComanda.isPending}
      />
    </div>
  );
}
