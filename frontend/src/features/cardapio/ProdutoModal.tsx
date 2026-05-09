import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
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
import { useCategorias, flattenCategorias } from "@/features/cadastros/categorias/useCategorias";
import { useInsumos } from "@/features/estoque/useInsumos";
import {
  useCreateProduto,
  useUpdateProduto,
  type ProdutoResponse,
} from "@/features/cadastros/produtos/useProdutos";
import { produtoSchema, type ProdutoFormValues } from "./produtoSchemas";

interface Props {
  open: boolean;
  onClose: () => void;
  editing?: ProdutoResponse | null;
}

function calcCmv(ficha: ProdutoFormValues["ficha_tecnica"], preco: string | undefined, insumos: ReturnType<typeof useInsumos>["data"]) {
  if (!ficha?.length || !insumos) return null;
  let custo = 0;
  for (const item of ficha) {
    const insumo = insumos.find((i) => i.id === item.insumo_id);
    if (!insumo || insumo.custo_medio === null) return null;
    const qty = parseFloat(item.quantidade);
    if (isNaN(qty)) return null;
    custo += insumo.custo_medio * qty;
  }
  const precoNum = parseFloat(preco ?? "");
  if (!precoNum) return { custo };
  return { custo, cmv: (custo / precoNum) * 100 };
}

function cmvColor(cmv: number): string {
  if (cmv < 30) return "text-green-600";
  if (cmv <= 50) return "text-yellow-600";
  return "text-red-600";
}

export function ProdutoModal({ open, onClose, editing }: Props) {
  const create = useCreateProduto();
  const update = useUpdateProduto();
  const { data: categoriasTree = [] } = useCategorias();
  const categorias = flattenCategorias(categoriasTree);
  const { data: insumos = [] } = useInsumos();

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<ProdutoFormValues>({
    resolver: zodResolver(produtoSchema),
    defaultValues: { ficha_tecnica: [] },
  });

  const { fields, append, remove } = useFieldArray({ control, name: "ficha_tecnica" });
  const watchedFicha = useWatch({ control, name: "ficha_tecnica" });
  const watchedPreco = useWatch({ control, name: "preco_venda" });

  useEffect(() => {
    if (editing) {
      reset({
        nome: editing.nome,
        categoria_id: editing.categoria_id ?? undefined,
        preco_venda: editing.preco_venda?.toString() ?? "",
        ficha_tecnica: editing.ficha_tecnica?.map((f) => ({
          insumo_id: f.insumo_id,
          quantidade: f.quantidade.toString(),
        })) ?? [],
      });
    } else {
      reset({ nome: "", categoria_id: null, preco_venda: "", ficha_tecnica: [] });
    }
  }, [editing, open, reset]);

  const isPending = create.isPending || update.isPending;

  const calc = calcCmv(watchedFicha, watchedPreco, insumos);

  function onSubmit(data: ProdutoFormValues) {
    const payload = {
      nome: data.nome,
      categoria_id: data.categoria_id ?? null,
      preco_venda: data.preco_venda || null,
      ficha_tecnica: data.ficha_tecnica?.map((f) => ({
        insumo_id: f.insumo_id,
        quantidade: f.quantidade,
      })) ?? [],
    };
    if (editing) {
      update.mutate({ id: editing.id, data: payload }, { onSuccess: onClose });
    } else {
      create.mutate(payload, { onSuccess: onClose });
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{editing ? "Editar Produto" : "Novo Produto"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="nome">Nome</Label>
            <Input id="nome" {...register("nome")} />
            {errors.nome && <p className="text-sm text-red-500">{errors.nome.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label>Categoria</Label>
              <select
                className="w-full rounded border px-2 py-1 text-sm"
                {...register("categoria_id", { setValueAs: (v) => (v === "" ? null : Number(v)) })}
              >
                <option value="">— Sem categoria —</option>
                {categorias.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.indent ? `  ${c.nome}` : c.nome}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <Label htmlFor="preco_venda">Preço de Venda (R$)</Label>
              <Input id="preco_venda" type="number" step="0.01" min="0" {...register("preco_venda")} />
              {errors.preco_venda && <p className="text-sm text-red-500">{errors.preco_venda.message}</p>}
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Ficha Técnica</Label>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => append({ insumo_id: 0, quantidade: "" })}
              >
                + Insumo
              </Button>
            </div>

            {fields.map((field, idx) => (
              <div key={field.id} className="flex gap-2 items-start">
                <select
                  className="flex-1 rounded border px-2 py-1 text-sm"
                  {...register(`ficha_tecnica.${idx}.insumo_id`, { setValueAs: (v) => Number(v) })}
                >
                  <option value={0}>Selecione insumo</option>
                  {insumos.map((i) => (
                    <option key={i.id} value={i.id}>
                      {i.nome} ({i.unidade_base})
                    </option>
                  ))}
                </select>
                <Input
                  className="w-24"
                  type="number"
                  step="0.001"
                  min="0.001"
                  placeholder="Qtd"
                  {...register(`ficha_tecnica.${idx}.quantidade`)}
                />
                <Button type="button" size="sm" variant="outline" onClick={() => remove(idx)}>
                  ✕
                </Button>
              </div>
            ))}
          </div>

          {calc && (
            <div className="rounded bg-gray-50 px-3 py-2 text-sm space-y-1">
              <span className="text-gray-600">Custo da ficha: </span>
              <span className="font-medium">R$ {calc.custo.toFixed(2)}</span>
              {calc.cmv !== undefined && (
                <>
                  <span className="text-gray-600 ml-3">CMV: </span>
                  <span className={`font-medium ${cmvColor(calc.cmv)}`}>{calc.cmv.toFixed(1)}%</span>
                </>
              )}
            </div>
          )}

          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>Cancelar</Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? "Salvando..." : "Salvar"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
