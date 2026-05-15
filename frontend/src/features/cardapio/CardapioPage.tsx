import React, { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Pagination, paginar } from "@/components/ui/pagination";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { useCategorias, flattenCategorias } from "@/features/cadastros/categorias/useCategorias";
import {
  useProdutos,
  useDesativarProduto,
  useReativarProduto,
  useDeleteProduto,
  type ProdutoResponse,
} from "@/features/cadastros/produtos/useProdutos";
import type { Categoria } from "@/features/cadastros/categorias/useCategorias";
import { ProdutoModal } from "./ProdutoModal";

type FiltroAtivo = "ativos" | "inativos" | "todos";

function buildCategoryPaths(tree: Categoria[], prefix = ""): Record<number, string> {
  const result: Record<number, string> = {};
  for (const cat of tree) {
    const path = prefix ? `${prefix} > ${cat.nome}` : cat.nome;
    result[cat.id] = path;
    if (cat.children?.length) {
      Object.assign(result, buildCategoryPaths(cat.children, path));
    }
  }
  return result;
}

function collectIds(id: number, tree: Categoria[]): Set<number> {
  const ids = new Set<number>([id]);
  for (const c of tree) {
    if (c.id === id) {
      for (const ch of c.children ?? []) {
        ids.add(ch.id);
        for (const gch of ch.children ?? []) ids.add(gch.id);
      }
    } else {
      for (const ch of c.children ?? []) {
        if (ch.id === id) {
          for (const gch of ch.children ?? []) ids.add(gch.id);
        }
      }
    }
  }
  return ids;
}

const POR_PAGINA = 10;

function calcCusto(produto: ProdutoResponse): number | null {
  if (!produto.ficha_tecnica?.length) return null;
  let total = 0;
  for (const item of produto.ficha_tecnica) {
    if (item.custo_medio_insumo === null) return null;
    total += Number(item.custo_medio_insumo) * Number(item.quantidade);
  }
  return total;
}

function CmvBadge({ preco, custo }: { preco: number | null; custo: number | null }) {
  if (custo === null || !preco) return <span className="text-gray-400">—</span>;
  const cmv = (custo / preco) * 100;
  const cls = cmv < 30 ? "text-green-600" : cmv <= 50 ? "text-yellow-600" : "text-red-600";
  return <span className={`font-medium ${cls}`}>{cmv.toFixed(1)}%</span>;
}

export function CardapioPage() {
  const { data: produtos = [], isLoading } = useProdutos();
  const { data: categorias = [] } = useCategorias();
  const desativar = useDesativarProduto();
  const reativar = useReativarProduto();
  const deletar = useDeleteProduto();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<ProdutoResponse | null>(null);
  const [confirmDesativar, setConfirmDesativar] = useState<number | null>(null);
  const [confirmDeletar, setConfirmDeletar] = useState<number | null>(null);
  const [filtro, setFiltro] = useState<FiltroAtivo>("ativos");
  const [busca, setBusca] = useState("");
  const [catFiltro, setCatFiltro] = useState<number | null>(null);
  const [expandidos, setExpandidos] = useState<Set<number>>(new Set());
  const [pagina, setPagina] = useState(1);

  function toggleExpand(id: number) {
    setExpandidos((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const catPathMap = buildCategoryPaths(categorias);

  const produtosFiltrados = produtos.filter((p) => {
    if (filtro === "ativos" && !p.ativo) return false;
    if (filtro === "inativos" && p.ativo) return false;
    if (busca && !p.nome.toLowerCase().includes(busca.toLowerCase())) return false;
    if (catFiltro !== null) {
      const ids = collectIds(catFiltro, categorias);
      if (!p.categoria_id || !ids.has(p.categoria_id)) return false;
    }
    return true;
  });

  function openCreate() {
    setEditing(null);
    setModalOpen(true);
  }

  function openEdit(p: ProdutoResponse) {
    setEditing(p);
    setModalOpen(true);
  }

  const filtroOpcoes: { value: FiltroAtivo; label: string }[] = [
    { value: "ativos", label: "Ativos" },
    { value: "inativos", label: "Inativos" },
    { value: "todos", label: "Todos" },
  ];

  return (
    <div className="p-6 min-h-full flex flex-col">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Cardápio</h1>
        <Button onClick={openCreate}>Novo Produto</Button>
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="flex rounded border overflow-hidden text-sm">
          {filtroOpcoes.map((o) => (
            <button
              key={o.value}
              onClick={() => { setFiltro(o.value); setPagina(1); }}
              className={`px-3 py-1.5 ${
                filtro === o.value
                  ? "bg-gray-900 text-white"
                  : "bg-white text-gray-600 hover:bg-gray-50"
              }`}
            >
              {o.label}
            </button>
          ))}
        </div>
        <select
          value={catFiltro ?? ""}
          onChange={(e) => { setCatFiltro(e.target.value ? Number(e.target.value) : null); setPagina(1); }}
          className="rounded border px-2 py-1.5 text-sm text-gray-700"
        >
          <option value="">Todas as categorias</option>
          {flattenCategorias(categorias).map((c) => (
            <option key={c.id} value={c.id}>
              {c.indent ? `  ${c.nome}` : c.nome}
            </option>
          ))}
        </select>
        <Input
          placeholder="Buscar produto..."
          value={busca}
          onChange={(e) => { setBusca(e.target.value); setPagina(1); }}
          className="w-52 text-sm"
        />
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      ) : produtosFiltrados.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum produto encontrado.</p>
      ) : (
        <div className="flex-1 flex flex-col">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2 pr-2 w-6" />
              <th className="py-2 pr-4">Nome</th>
              <th className="py-2 pr-4">Categoria</th>
              <th className="py-2 pr-4 text-right">Preço</th>
              <th className="py-2 pr-4 text-right">Custo Ficha</th>
              <th className="py-2 pr-4 text-right">CMV%</th>
              <th className="py-2 pr-4 text-right">Lucro Bruto</th>
              <th className="py-2 pr-4 text-right">Produção</th>
              <th className="py-2" />
            </tr>
          </thead>
          <tbody>
            {paginar(produtosFiltrados, pagina, POR_PAGINA).map((p) => {
              const custo = calcCusto(p);
              const lucro =
                p.preco_venda !== null && custo !== null ? p.preco_venda - custo : null;
              const expandido = expandidos.has(p.id);
              const temFicha = p.ficha_tecnica && p.ficha_tecnica.length > 0;

              return (
                <React.Fragment key={p.id}>
                  <tr className={`border-b ${!expandido ? "last:border-0" : ""} ${!p.ativo ? "opacity-50" : ""}`}>
                    <td className="py-2 pr-2">
                      <button
                        type="button"
                        onClick={() => toggleExpand(p.id)}
                        className="text-gray-400 hover:text-gray-700 disabled:invisible"
                        disabled={!temFicha}
                        title={temFicha ? "Ver insumos" : "Sem ficha técnica"}
                      >
                        {expandido
                          ? <ChevronDown size={14} />
                          : <ChevronRight size={14} />}
                      </button>
                    </td>
                    <td className="py-2 pr-4 font-medium">{p.nome}</td>
                    <td className="py-2 pr-4 text-gray-500">
                      {p.categoria_id ? (catPathMap[p.categoria_id] ?? "—") : "—"}
                    </td>
                    <td className="py-2 pr-4 text-right">
                      {p.preco_venda !== null ? `R$ ${Number(p.preco_venda).toFixed(2)}` : "—"}
                    </td>
                    <td className="py-2 pr-4 text-right">
                      {custo !== null ? `R$ ${custo.toFixed(2)}` : "—"}
                    </td>
                    <td className="py-2 pr-4 text-right">
                      <CmvBadge preco={p.preco_venda} custo={custo} />
                    </td>
                    <td className="py-2 pr-4 text-right">
                      {lucro !== null ? (
                        <span className={lucro >= 0 ? "text-green-600" : "text-red-600"}>
                          R$ {lucro.toFixed(2)}
                        </span>
                      ) : "—"}
                    </td>
                    <td className="py-2 pr-4 text-right">
                      {p.producao_possivel === null ? (
                        <span className="text-gray-400">—</span>
                      ) : p.producao_possivel === 0 ? (
                        <span className="font-medium text-red-600">0</span>
                      ) : (
                        <span className="text-gray-700">{p.producao_possivel}</span>
                      )}
                    </td>
                    <td className="py-2 text-right space-x-2">
                      <Button size="sm" variant="outline" onClick={() => openEdit(p)}>
                        Editar
                      </Button>
                      {p.ativo ? (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setConfirmDesativar(p.id)}
                          className="text-yellow-600 hover:text-yellow-700"
                        >
                          Desativar
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => reativar.mutate(p.id)}
                          className="text-green-600 hover:text-green-700"
                        >
                          Reativar
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setConfirmDeletar(p.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        Remover
                      </Button>
                    </td>
                  </tr>

                  {expandido && temFicha && (
                    <tr className="border-b last:border-0 bg-gray-50">
                      <td />
                      <td colSpan={8} className="py-2 px-2 pb-3">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="text-gray-400 border-b border-gray-200">
                              <th className="py-1 pr-4 text-left font-medium">Insumo</th>
                              <th className="py-1 pr-4 text-right font-medium">Quantidade</th>
                              <th className="py-1 pr-4 text-right font-medium">Custo médio</th>
                              <th className="py-1 text-right font-medium">Custo total</th>
                            </tr>
                          </thead>
                          <tbody>
                            {p.ficha_tecnica!.map((ft) => {
                              const custoMedio = ft.custo_medio_insumo !== null ? Number(ft.custo_medio_insumo) : null;
                              const qtd = Number(ft.quantidade);
                              const custoItem = custoMedio !== null ? custoMedio * qtd : null;
                              return (
                                <tr key={ft.insumo_id} className="border-b border-gray-100 last:border-0">
                                  <td className="py-1 pr-4 text-gray-700">{ft.insumo_nome}</td>
                                  <td className="py-1 pr-4 text-right text-gray-600">
                                    {ft.unidade_base === "kg"
                                      ? qtd.toFixed(3)
                                      : Math.round(qtd).toString()}{" "}
                                    {ft.unidade_base}
                                  </td>
                                  <td className="py-1 pr-4 text-right text-gray-600">
                                    {custoMedio !== null ? `R$ ${custoMedio.toFixed(4)}` : "—"}
                                  </td>
                                  <td className="py-1 text-right text-gray-700">
                                    {custoItem !== null ? `R$ ${custoItem.toFixed(4)}` : "—"}
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
        <div className="flex-1" />
        <Pagination
          pagina={pagina}
          totalPaginas={Math.ceil(produtosFiltrados.length / POR_PAGINA)}
          total={produtosFiltrados.length}
          label="produtos"
          onPageChange={setPagina}
        />
        </div>
      )}

      <ProdutoModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        editing={editing}
      />

      <ConfirmDialog
        open={confirmDesativar !== null}
        title="Desativar produto?"
        confirmLabel="Desativar"
        onConfirm={() => {
          desativar.mutate(confirmDesativar!);
          setConfirmDesativar(null);
        }}
        onCancel={() => setConfirmDesativar(null)}
        isPending={desativar.isPending}
      />

      <ConfirmDialog
        open={confirmDeletar !== null}
        title="Remover produto?"
        confirmLabel="Remover"
        onConfirm={() => {
          deletar.mutate(confirmDeletar!);
          setConfirmDeletar(null);
        }}
        onCancel={() => setConfirmDeletar(null)}
        isPending={deletar.isPending}
      />
    </div>
  );
}
