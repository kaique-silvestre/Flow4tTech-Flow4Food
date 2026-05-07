import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useMemo } from "react";
import { useFieldArray, useForm, useWatch } from "react-hook-form";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCategorias } from "@/features/cadastros/categorias/useCategorias";
import { formatCurrency } from "@/lib/format";
import { itemSchema, type ItemFormValues } from "./itemSchemas";
import { useCreateItem, useItensSimples, useUpdateItem, type ItemResponse } from "./useItens";

interface Props {
  open: boolean;
  onClose: () => void;
  editing?: ItemResponse | null;
}

export function ItemModal({ open, onClose, editing }: Props) {
  const create = useCreateItem();
  const update = useUpdateItem();
  const { data: categorias = [] } = useCategorias();
  const { data: insumosSimples = [] } = useItensSimples();

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<ItemFormValues>({
    resolver: zodResolver(itemSchema),
    defaultValues: { tipo: "simples", vendavel: false, unidade_base: "un" },
  });

  const { fields, append, remove } = useFieldArray({ control, name: "ficha_tecnica" });

  useEffect(() => {
    if (open) {
      reset(
        editing
          ? {
              nome: editing.nome,
              categoria_id: editing.categoria_id ?? undefined,
              tipo: editing.tipo,
              vendavel: editing.vendavel,
              unidade_base: editing.unidade_base,
              quantidade_caixa: editing.quantidade_caixa ?? undefined,
              preco_venda: editing.preco_venda ?? undefined,
              ficha_tecnica: editing.componentes?.map((c) => ({
                insumo_id: c.insumo_id,
                quantidade: c.quantidade,
              })) ?? [],
            }
          : { tipo: "simples", vendavel: false, unidade_base: "un", ficha_tecnica: [] }
      );
    }
  }, [editing, open, reset]);

  const tipo = useWatch({ control, name: "tipo" });
  const vendavel = useWatch({ control, name: "vendavel" });
  const unidadeBase = useWatch({ control, name: "unidade_base" });
  const precoVenda = useWatch({ control, name: "preco_venda" });
  const fichaWatch = useWatch({ control, name: "ficha_tecnica" });

  const custoCalculado = useMemo(() => {
    if (tipo !== "composto" || !fichaWatch?.length) return null;
    let total = 0;
    for (const comp of fichaWatch) {
      const insumo = insumosSimples.find((i) => i.id === Number(comp.insumo_id));
      if (!insumo || insumo.custo_medio == null) return null;
      total += Number(comp.quantidade || 0) * Number(insumo.custo_medio);
    }
    return total;
  }, [tipo, fichaWatch, insumosSimples]);

  const cmvPercentual = useMemo(() => {
    if (custoCalculado == null || !precoVenda || Number(precoVenda) <= 0) return null;
    return (custoCalculado / Number(precoVenda)) * 100;
  }, [custoCalculado, precoVenda]);

  const isPending = create.isPending || update.isPending;

  function onSubmit(data: ItemFormValues) {
    const payload = {
      ...data,
      categoria_id: data.categoria_id ?? null,
      quantidade_caixa: data.quantidade_caixa ?? null,
      preco_venda: data.preco_venda ?? null,
      ficha_tecnica: tipo === "composto" ? (data.ficha_tecnica ?? []) : [],
    };
    if (editing) {
      update.mutate({ id: editing.id, data: payload }, { onSuccess: onClose });
    } else {
      create.mutate(payload, { onSuccess: onClose });
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{editing ? "Editar Item" : "Novo Item"}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Nome */}
          <div className="space-y-1">
            <Label htmlFor="nome">Nome</Label>
            <Input id="nome" {...register("nome")} />
            {errors.nome && <p className="text-sm text-red-500">{errors.nome.message}</p>}
          </div>

          {/* Categoria */}
          <div className="space-y-1">
            <Label htmlFor="categoria_id">Categoria</Label>
            <select
              id="categoria_id"
              className="w-full rounded border px-2 py-1.5 text-sm"
              {...register("categoria_id", { setValueAs: (v) => (v === "" ? undefined : Number(v)) })}
            >
              <option value="">Nenhuma</option>
              {categorias.map((c) => (
                <option key={c.id} value={c.id}>{c.nome}</option>
              ))}
            </select>
          </div>

          {/* Tipo */}
          <div className="space-y-1">
            <Label>Tipo</Label>
            <div className="flex gap-4 text-sm">
              {(["simples", "composto"] as const).map((t) => (
                <label key={t} className="flex cursor-pointer items-center gap-1">
                  <input type="radio" value={t} {...register("tipo")} />
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </label>
              ))}
            </div>
          </div>

          {/* Vendável */}
          <div className="flex items-center gap-2">
            <input type="checkbox" id="vendavel" {...register("vendavel")} className="h-4 w-4" />
            <Label htmlFor="vendavel" className="cursor-pointer">Vendável</Label>
          </div>

          {/* Preço de venda (condicional) */}
          {vendavel && (
            <div className="space-y-1">
              <Label htmlFor="preco_venda">Preço de venda (R$)</Label>
              <Input
                id="preco_venda"
                type="number"
                step="0.01"
                min="0"
                {...register("preco_venda")}
              />
              {errors.preco_venda && (
                <p className="text-sm text-red-500">{errors.preco_venda.message}</p>
              )}
            </div>
          )}

          {/* Unidade base */}
          <div className="space-y-1">
            <Label>Unidade base</Label>
            <div className="flex gap-4 text-sm">
              <label className="flex cursor-pointer items-center gap-1">
                <input type="radio" value="un" {...register("unidade_base")} />
                Unidade (un)
              </label>
              <label className="flex cursor-pointer items-center gap-1">
                <input type="radio" value="g" {...register("unidade_base")} />
                Grama (g)
              </label>
            </div>
          </div>

          {/* Quantidade por caixa (condicional: só se unidade=un) */}
          {unidadeBase === "un" && (
            <div className="space-y-1">
              <Label htmlFor="quantidade_caixa">Quantidade por caixa</Label>
              <Input
                id="quantidade_caixa"
                type="number"
                min="1"
                step="1"
                placeholder="Opcional"
                {...register("quantidade_caixa")}
              />
              {errors.quantidade_caixa && (
                <p className="text-sm text-red-500">{errors.quantidade_caixa.message}</p>
              )}
            </div>
          )}

          {/* Ficha técnica (condicional: só se tipo=composto) */}
          {tipo === "composto" && (
            <div className="space-y-2 rounded border p-3">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-semibold">Ficha Técnica</Label>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => append({ insumo_id: 0, quantidade: 0 })}
                >
                  + Adicionar insumo
                </Button>
              </div>

              {fields.length === 0 && (
                <p className="text-xs text-gray-400">Nenhum insumo adicionado.</p>
              )}

              {fields.map((field, index) => {
                const insumoId = fichaWatch?.[index]?.insumo_id;
                const insumo = insumosSimples.find((i) => i.id === Number(insumoId));
                return (
                  <div key={field.id} className="flex items-end gap-2">
                    <div className="flex-1 space-y-1">
                      <Label className="text-xs">Insumo</Label>
                      <select
                        className="w-full rounded border px-2 py-1.5 text-sm"
                        {...register(`ficha_tecnica.${index}.insumo_id`, {
                          setValueAs: (v) => Number(v),
                        })}
                      >
                        <option value={0}>Selecione...</option>
                        {insumosSimples.map((i) => (
                          <option key={i.id} value={i.id}>{i.nome}</option>
                        ))}
                      </select>
                      {errors.ficha_tecnica?.[index]?.insumo_id && (
                        <p className="text-xs text-red-500">
                          {errors.ficha_tecnica[index]?.insumo_id?.message}
                        </p>
                      )}
                    </div>
                    <div className="w-28 space-y-1">
                      <Label className="text-xs">Quantidade</Label>
                      <Input
                        type="number"
                        step="0.001"
                        min="0"
                        {...register(`ficha_tecnica.${index}.quantidade`)}
                      />
                      {errors.ficha_tecnica?.[index]?.quantidade && (
                        <p className="text-xs text-red-500">
                          {errors.ficha_tecnica[index]?.quantidade?.message}
                        </p>
                      )}
                    </div>
                    <div className="w-12 space-y-1">
                      <Label className="text-xs">Und.</Label>
                      <p className="py-1.5 text-sm text-gray-500">{insumo?.unidade_base ?? "—"}</p>
                    </div>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      className="mb-0 text-red-500 hover:text-red-700"
                      onClick={() => remove(index)}
                    >
                      ✕
                    </Button>
                  </div>
                );
              })}

              {/* Custo calculado */}
              {custoCalculado != null && (
                <div className="mt-2 rounded bg-gray-50 px-3 py-2 text-sm">
                  <span className="text-gray-500">Custo calculado: </span>
                  <span className="font-medium">{formatCurrency(custoCalculado)}</span>
                  {cmvPercentual != null && (
                    <span className="ml-3 text-gray-500">
                      CMV: <span className="font-medium">{cmvPercentual.toFixed(1)}%</span>
                    </span>
                  )}
                </div>
              )}
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? "Salvando..." : "Salvar"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
