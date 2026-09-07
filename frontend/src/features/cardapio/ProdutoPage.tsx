import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { useBreadcrumbLabel } from "@/components/layout/Breadcrumb";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { useCategorias } from "@/features/cadastros/categorias/useCategorias";
import { buildCategoryPaths } from "./CategoriaFilterPopover";
import {
  useProdutos,
  useUpdateProduto,
  useDesativarProduto,
  useReativarProduto,
  custoItemFicha,
  type ProdutoResponse,
  type ProdutoUpdateRequest,
} from "@/features/cadastros/produtos/useProdutos";

/** Builds the update payload for removing a single ficha técnica item, keeping the rest of the product unchanged. */
export function buildFichaRemovalPayload(produto: ProdutoResponse, insumoId: number): ProdutoUpdateRequest {
  return {
    nome: produto.nome,
    categoria_id: produto.categoria_id,
    preco_venda: produto.preco_venda !== null ? String(produto.preco_venda) : null,
    ficha_tecnica: (produto.ficha_tecnica ?? [])
      .filter((item) => item.insumo_id !== insumoId)
      .map((item) => ({ insumo_id: item.insumo_id, quantidade: String(item.quantidade) })),
  };
}

export function ProdutoPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const produtoId = Number(id);

  const { data: produtosData, isLoading } = useProdutos();
  const produto = produtosData?.itens.find((p) => p.id === produtoId);

  const { data: categoriasTree = [] } = useCategorias();
  const catPathMap = buildCategoryPaths(categoriasTree);

  const update = useUpdateProduto();
  const desativar = useDesativarProduto();
  const reativar = useReativarProduto();
  const [confirmDesativar, setConfirmDesativar] = useState(false);

  useBreadcrumbLabel(produto?.nome);

  function removerInsumo(insumoId: number) {
    if (!produto) return;
    update.mutate({ id: produto.id, data: buildFichaRemovalPayload(produto, insumoId) });
  }

  if (isLoading) {
    return (
      <div className="p-4 lg:p-6">
        <div className="h-8 w-48 animate-pulse rounded bg-gray-100" />
      </div>
    );
  }

  if (!produto) {
    return (
      <div className="p-4 lg:p-6">
        <button
          onClick={() => navigate("/cardapio")}
          className="mb-4 flex h-9 w-9 items-center justify-center rounded border text-gray-600 hover:bg-gray-50"
        >
          <ArrowLeft size={18} />
        </button>
        <p className="text-sm text-gray-500">Produto não encontrado.</p>
      </div>
    );
  }

  const ficha = produto.ficha_tecnica ?? [];

  return (
    <div className="p-4 lg:p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate("/cardapio")}
            className="flex h-9 w-9 items-center justify-center rounded border text-gray-600 hover:bg-gray-50"
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <h1 className="text-xl font-semibold">{produto.nome}</h1>
            <p className="text-sm text-gray-500">
              {produto.categoria_id ? (catPathMap[produto.categoria_id] ?? "—") : "Sem categoria"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold">
            {produto.preco_venda !== null ? `R$ ${Number(produto.preco_venda).toFixed(2)}` : "—"}
          </span>
          {produto.ativo ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setConfirmDesativar(true)}
              className="text-yellow-600 hover:text-yellow-700"
            >
              Desativar
            </Button>
          ) : (
            <Button
              size="sm"
              variant="outline"
              onClick={() => reativar.mutate(produto.id)}
              className="text-green-600 hover:text-green-700"
            >
              Reativar
            </Button>
          )}
        </div>
      </div>

      <h2 className="mb-2 text-sm font-medium text-gray-700">Ficha Técnica</h2>
      {ficha.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum insumo cadastrado.</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Insumo</TableHead>
              <TableHead className="text-right">Quantidade</TableHead>
              <TableHead>Unidade</TableHead>
              <TableHead className="text-right">Custo</TableHead>
              <TableHead className="w-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {ficha.map((item) => {
              const qtd = Number(item.quantidade);
              const custoItem = custoItemFicha(item);
              return (
                <TableRow key={item.insumo_id}>
                  <TableCell className="font-medium">{item.insumo_nome}</TableCell>
                  <TableCell className="text-right">
                    {item.unidade_base === "kg" ? qtd.toFixed(3) : Math.round(qtd).toString()}
                  </TableCell>
                  <TableCell>{item.unidade_base}</TableCell>
                  <TableCell className="text-right">
                    {custoItem !== null ? `R$ ${custoItem.toFixed(4)}` : "—"}
                  </TableCell>
                  <TableCell>
                    <Button size="sm" variant="outline" onClick={() => removerInsumo(item.insumo_id)}>
                      ✕
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      )}

      <ConfirmDialog
        open={confirmDesativar}
        title="Desativar produto?"
        confirmLabel="Desativar"
        onConfirm={() => {
          desativar.mutate(produto.id);
          setConfirmDesativar(false);
        }}
        onCancel={() => setConfirmDesativar(false)}
        isPending={desativar.isPending}
      />
    </div>
  );
}
