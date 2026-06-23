import { useEffect, useRef, useState } from "react";
import { Trash2, X } from "lucide-react";
import { useDebounce } from "use-debounce";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useProdutos, type ProdutoResponse } from "@/features/cadastros/produtos/useProdutos";
import { useUsers } from "@/features/configuracoes/usuarios/useUsers";
import { formatCurrency } from "@/lib/format";
import { useLancarConsumoBatch } from "./useConsumoInterno";

interface CartItem {
  produto: ProdutoResponse;
  quantidade: string;
  observacao: string;
}

function calcularCustoUnitario(produto: ProdutoResponse): number {
  const ft = produto.ficha_tecnica;
  if (ft && ft.length > 0) {
    const custo = ft.reduce(
      (acc, item) => acc + item.quantidade * (item.custo_medio_insumo ?? 0),
      0,
    );
    if (custo > 0) return custo;
  }
  return produto.preco_venda ?? 0;
}

interface Props {
  open: boolean;
  consumidorId?: number;
  onClose: () => void;
}

export function LancarConsumoModal({ open, consumidorId, onClose }: Props) {
  const [consumidorIdSelecionado, setConsumidorIdSelecionado] = useState<number | null>(
    consumidorId ?? null,
  );

  // Add-item form
  const [produtoSearch, setProdutoSearch] = useState("");
  const [produtoSelecionado, setProdutoSelecionado] = useState<ProdutoResponse | null>(null);
  const [dropdownAberto, setDropdownAberto] = useState(false);
  const [quantidade, setQuantidade] = useState("");
  const [observacao, setObservacao] = useState("");

  // Cart
  const [cart, setCart] = useState<CartItem[]>([]);

  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const [debouncedSearch] = useDebounce(produtoSearch, 300);
  const { data: produtosData } = useProdutos(debouncedSearch || undefined, {
    ativo: true,
    por_pagina: 20,
  });
  const produtos = produtosData?.itens ?? [];

  const { data: usuarios = [] } = useUsers();
  const ativos = usuarios.filter((u) => u.is_active);

  const lancar = useLancarConsumoBatch();

  const consumidorEfetivo = consumidorId ?? consumidorIdSelecionado;

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownAberto(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function reset() {
    if (!consumidorId) setConsumidorIdSelecionado(null);
    setProdutoSearch("");
    setProdutoSelecionado(null);
    setDropdownAberto(false);
    setQuantidade("");
    setObservacao("");
    setCart([]);
  }

  function handleSelectProduto(produto: ProdutoResponse) {
    setProdutoSelecionado(produto);
    setProdutoSearch("");
    setDropdownAberto(false);
  }

  function handleClearProduto() {
    setProdutoSelecionado(null);
    setProdutoSearch("");
    setDropdownAberto(false);
    setTimeout(() => inputRef.current?.focus(), 0);
  }

  function handleAddToCart() {
    if (!produtoSelecionado || !quantidade || Number(quantidade) <= 0) return;
    const novaQtd = Number(quantidade);
    setCart((prev) => {
      const idx = prev.findIndex((item) => item.produto.id === produtoSelecionado!.id);
      if (idx !== -1) {
        const updated = [...prev];
        const soma = parseFloat((Number(updated[idx].quantidade) + novaQtd).toFixed(4)).toString();
        updated[idx] = { ...updated[idx], quantidade: soma };
        return updated;
      }
      return [...prev, { produto: produtoSelecionado!, quantidade, observacao }];
    });
    setProdutoSelecionado(null);
    setProdutoSearch("");
    setQuantidade("");
    setObservacao("");
  }

  function handleRemoveFromCart(index: number) {
    setCart((prev) => prev.filter((_, i) => i !== index));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!consumidorEfetivo || cart.length === 0) return;
    lancar.mutate(
      {
        consumidor_id: consumidorEfetivo,
        itens: cart.map((item) => ({
          produto_id: item.produto.id,
          quantidade: Number(item.quantidade),
          observacao: item.observacao.trim() || undefined,
        })),
      },
      {
        onSuccess: () => {
          reset();
          onClose();
        },
      },
    );
  }

  function handleOpenChange(v: boolean) {
    if (!v) {
      reset();
      onClose();
    }
  }

  const custoPreview =
    produtoSelecionado && Number(quantidade) > 0
      ? { unit: calcularCustoUnitario(produtoSelecionado), subtotal: calcularCustoUnitario(produtoSelecionado) * Number(quantidade) }
      : null;

  const totalGeral = cart.reduce(
    (acc, item) => acc + calcularCustoUnitario(item.produto) * Number(item.quantidade),
    0,
  );

  const canAdd = produtoSelecionado !== null && Number(quantidade) > 0;
  const canSubmit = consumidorEfetivo !== null && cart.length > 0;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Lançar Consumo</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Consumidor — only when not pre-selected */}
          {!consumidorId && (
            <div>
              <Label>Consumidor</Label>
              <Select
                value={consumidorIdSelecionado ? String(consumidorIdSelecionado) : ""}
                onValueChange={(v) => setConsumidorIdSelecionado(Number(v))}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Selecione o consumidor" />
                </SelectTrigger>
                <SelectContent>
                  {ativos.map((u) => (
                    <SelectItem key={u.id} value={String(u.id)}>
                      {u.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Add-item form */}
          <div className="rounded border bg-gray-50 p-3">
            <p className="mb-2 text-sm font-medium text-gray-700">Adicionar produto</p>

            {/* Product combobox */}
            <div className="mb-2">
              <Label className="text-xs text-gray-500">Produto</Label>
              <div className="relative mt-1" ref={dropdownRef}>
                {produtoSelecionado ? (
                  <div className="flex items-center gap-2 rounded border border-input bg-background px-3 py-2 text-sm">
                    <span className="flex-1 truncate">{produtoSelecionado.nome}</span>
                    <button
                      type="button"
                      onClick={handleClearProduto}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ) : (
                  <Input
                    ref={inputRef}
                    placeholder="Buscar produto..."
                    value={produtoSearch}
                    autoComplete="off"
                    onChange={(e) => {
                      setProdutoSearch(e.target.value);
                      setDropdownAberto(true);
                    }}
                    onFocus={() => setDropdownAberto(true)}
                  />
                )}
                {dropdownAberto && !produtoSelecionado && produtos.length > 0 && (
                  <div className="absolute z-50 mt-1 max-h-48 w-full overflow-auto rounded border border-gray-200 bg-white shadow-lg">
                    {produtos.map((p) => (
                      <button
                        key={p.id}
                        type="button"
                        className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100"
                        onMouseDown={(e) => {
                          e.preventDefault();
                          handleSelectProduto(p);
                        }}
                      >
                        {p.nome}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Quantidade + observação */}
            <div className="flex gap-2">
              <div className="w-28">
                <Label className="text-xs text-gray-500">Quantidade</Label>
                <Input
                  type="number"
                  min="0.01"
                  step="0.01"
                  placeholder="Ex: 1"
                  value={quantidade}
                  onChange={(e) => setQuantidade(e.target.value)}
                  className="mt-1"
                />
              </div>
              <div className="flex-1">
                <Label className="text-xs text-gray-500">Observação (opcional)</Label>
                <Input
                  placeholder="Ex: almoço"
                  value={observacao}
                  onChange={(e) => setObservacao(e.target.value)}
                  className="mt-1"
                />
              </div>
            </div>

            {/* Custo preview */}
            {custoPreview && (
              <p className="mt-2 text-xs text-gray-500">
                Custo unit.:{" "}
                <span className="text-gray-700">{formatCurrency(custoPreview.unit)}</span>
                {"  ·  "}Subtotal:{" "}
                <span className="font-medium text-gray-800">
                  {formatCurrency(custoPreview.subtotal)}
                </span>
              </p>
            )}

            <Button
              type="button"
              variant="outline"
              className="mt-3 w-full"
              disabled={!canAdd}
              onClick={handleAddToCart}
            >
              + Adicionar ao lote
            </Button>
          </div>

          {/* Cart */}
          {cart.length > 0 && (
            <div>
              <p className="mb-2 text-sm font-medium text-gray-700">
                Lote ({cart.length} {cart.length === 1 ? "item" : "itens"})
              </p>
              <div className="overflow-hidden rounded border">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50 text-left text-xs text-gray-500">
                      <th className="px-3 py-2 font-medium">Produto</th>
                      <th className="px-3 py-2 font-medium text-center">Qtd</th>
                      <th className="px-3 py-2 font-medium text-right">Subtotal</th>
                      <th className="px-2 py-2" />
                    </tr>
                  </thead>
                  <tbody>
                    {cart.map((item, i) => {
                      const subtotal =
                        calcularCustoUnitario(item.produto) * Number(item.quantidade);
                      return (
                        <tr key={i} className="border-b last:border-0">
                          <td className="px-3 py-2">
                            <div>{item.produto.nome}</div>
                            {item.observacao && (
                              <div className="text-xs text-gray-400">{item.observacao}</div>
                            )}
                          </td>
                          <td className="px-3 py-2 text-center">{item.quantidade}</td>
                          <td className="px-3 py-2 text-right">{formatCurrency(subtotal)}</td>
                          <td className="px-2 py-2">
                            <button
                              type="button"
                              onClick={() => handleRemoveFromCart(i)}
                              className="text-gray-400 hover:text-red-500"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                  <tfoot>
                    <tr className="border-t-2 bg-gray-50">
                      <td colSpan={2} className="px-3 py-2 text-right text-xs text-gray-500">
                        Total estimado:
                      </td>
                      <td className="px-3 py-2 text-right font-semibold">
                        {formatCurrency(totalGeral)}
                      </td>
                      <td />
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => handleOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={lancar.isPending || !canSubmit}>
              {lancar.isPending
                ? "Registrando..."
                : cart.length > 1
                  ? `Registrar (${cart.length})`
                  : "Registrar"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
