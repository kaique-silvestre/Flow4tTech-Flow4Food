import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { Controller, useFieldArray, useForm, useWatch } from "react-hook-form";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MoneyInput } from "@/components/ui/money-input";
import { useCategorias, flattenCategorias, type Categoria } from "@/features/cadastros/categorias/useCategorias";
import { CategoriaModal } from "@/features/cadastros/categorias/CategoriaModal";
import { useInsumos, type InsumoResponse } from "@/features/estoque/useInsumos";
import {
  useCreateProduto,
  useUpdateProduto,
  type ProdutoResponse,
} from "@/features/cadastros/produtos/useProdutos";
import { InsumoModal } from "@/features/compras/InsumoModal";
import { produtoSchema, type ProdutoFormValues } from "./produtoSchemas";
import { getFamilyOptions, toBase } from "@/lib/units";

interface Props {
  open: boolean;
  onClose: () => void;
  editing?: ProdutoResponse | null;
}

function calcCmv(
  ficha: ProdutoFormValues["ficha_tecnica"],
  preco: string | undefined,
  insumos: InsumoResponse[] | undefined,
  selectedUnits: string[]
) {
  if (!ficha?.length || !insumos) return null;
  let custo = 0;
  for (let i = 0; i < ficha.length; i++) {
    const item = ficha[i];
    const insumo = insumos.find((ins) => ins.id === item.insumo_id);
    if (!insumo || insumo.custo_medio === null) return null;
    const qty = parseFloat(item.quantidade);
    if (isNaN(qty)) return null;
    const opts = getFamilyOptions(insumo.unidade_base, insumo.quantidade_caixa);
    const selVal = selectedUnits[i] || insumo.unidade_base;
    const opt = opts.find((o) => o.value === selVal) ?? opts[0];
    custo += insumo.custo_medio * toBase(qty, opt);
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
  const qc = useQueryClient();
  const create = useCreateProduto();
  const update = useUpdateProduto();
  const { data: categoriasTree = [] } = useCategorias();
  const categorias = flattenCategorias(categoriasTree);
  const { data: insumosData } = useInsumos();
  const insumos = insumosData?.itens ?? [];

  const [selectedUnits, setSelectedUnits] = useState<string[]>([]);
  const [novoInsumoIdx, setNovoInsumoIdx] = useState<number | null>(null);
  const [novaCategOpen, setNovaCategOpen] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
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
      setSelectedUnits(
        editing.ficha_tecnica?.map((f) => {
          const ins = insumos.find((i) => i.id === f.insumo_id);
          return ins?.unidade_base ?? "";
        }) ?? []
      );
    } else {
      reset({ nome: "", categoria_id: undefined, preco_venda: "", ficha_tecnica: [] });
      setSelectedUnits([]);
    }
  }, [editing, open, reset]); // eslint-disable-line react-hooks/exhaustive-deps

  const isPending = create.isPending || update.isPending;

  function handleCategoriaCreated(cat: Categoria) {
    qc.setQueryData<Categoria[]>(["categorias"], (old = []) =>
      old.some((c) => c.id === cat.id) ? old : [...old, { ...cat, children: [] }]
    );
    setValue("categoria_id", cat.id as never);
  }

  function handleInsumoCreated(insumo: InsumoResponse) {
    if (novoInsumoIdx === null) return;
    qc.setQueryData<InsumoResponse[]>(["insumos", undefined], (old = []) =>
      old.some((i) => i.id === insumo.id) ? old : [...old, insumo]
    );
    setValue(`ficha_tecnica.${novoInsumoIdx}.insumo_id`, insumo.id);
    setSelectedUnits((prev) => {
      const next = [...prev];
      next[novoInsumoIdx] = insumo.unidade_base;
      return next;
    });
    setNovoInsumoIdx(null);
  }

  const calc = calcCmv(watchedFicha, watchedPreco, insumos, selectedUnits);

  function onSubmit(data: ProdutoFormValues) {
    const payload = {
      nome: data.nome,
      categoria_id: data.categoria_id ?? null,
      preco_venda: data.preco_venda || null,
      ficha_tecnica: data.ficha_tecnica?.map((f, i) => {
        const insumo = insumos.find((ins) => ins.id === f.insumo_id);
        if (!insumo) return { insumo_id: f.insumo_id, quantidade: f.quantidade };
        const opts = getFamilyOptions(insumo.unidade_base, insumo.quantidade_caixa);
        const selVal = selectedUnits[i] || insumo.unidade_base;
        const opt = opts.find((o) => o.value === selVal) ?? opts[0];
        const baseQty = toBase(parseFloat(f.quantidade) || 0, opt);
        return { insumo_id: f.insumo_id, quantidade: String(baseQty) };
      }) ?? [],
    };
    if (editing) {
      update.mutate({ id: editing.id, data: payload }, { onSuccess: onClose });
    } else {
      create.mutate(payload, { onSuccess: onClose });
    }
  }

  return (
    <>
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
                className={`w-full rounded border px-2 py-1 text-sm${errors.categoria_id ? " border-red-500" : ""}`}
                {...register("categoria_id", { setValueAs: (v) => (v === "" ? undefined : Number(v)) })}
              >
                <option value="">— Selecione uma categoria —</option>
                {categorias.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.indent ? `  ${c.nome}` : c.nome}
                  </option>
                ))}
              </select>
              {errors.categoria_id && (
                <p className="text-sm text-red-500">{errors.categoria_id.message}</p>
              )}
              <button
                type="button"
                className="text-xs text-blue-600 hover:underline mt-0.5"
                onClick={() => setNovaCategOpen(true)}
              >
                [ + Cadastrar nova categoria ]
              </button>
            </div>
            <div className="space-y-1">
              <Label htmlFor="preco_venda">Preço de Venda</Label>
              <Controller
                name="preco_venda"
                control={control}
                render={({ field }) => (
                  <MoneyInput
                    id="preco_venda"
                    value={field.value ?? ""}
                    onValueChange={(raw) => field.onChange(raw)}
                  />
                )}
              />
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
                onClick={() => {
                  append({ insumo_id: 0, quantidade: "" });
                  setSelectedUnits((prev) => [...prev, ""]);
                }}
              >
                + Insumo
              </Button>
            </div>

            {fields.map((field, idx) => {
              const insumoId = watchedFicha?.[idx]?.insumo_id;
              const insumo = insumos.find((i) => i.id === Number(insumoId));
              const opts = insumo ? getFamilyOptions(insumo.unidade_base, insumo.quantidade_caixa) : [];
              const selUnit = selectedUnits[idx] || insumo?.unidade_base || "";
              return (
                <div key={field.id} className="flex gap-2 items-start">
                  <div className="flex-1">
                    <select
                      className="w-full rounded border px-2 py-1 text-sm"
                      {...register(`ficha_tecnica.${idx}.insumo_id`, {
                        setValueAs: (v) => Number(v),
                        onChange: (e: React.ChangeEvent<HTMLSelectElement>) => {
                          const found = insumos.find((i) => i.id === Number(e.target.value));
                          setSelectedUnits((prev) => {
                            const next = [...prev];
                            next[idx] = found?.unidade_base ?? "";
                            return next;
                          });
                        },
                      })}
                    >
                      <option value={0}>Selecione insumo</option>
                      {insumos.map((i) => (
                        <option key={i.id} value={i.id}>
                          {i.nome} ({i.unidade_base})
                        </option>
                      ))}
                    </select>
                    {idx === fields.length - 1 && (
                      <button
                        type="button"
                        className="text-xs text-blue-600 hover:underline mt-0.5"
                        onClick={() => setNovoInsumoIdx(idx)}
                      >
                        [ + Cadastrar novo insumo ]
                      </button>
                    )}
                  </div>
                  <Input
                    className="w-20"
                    type="number"
                    step="0.001"
                    min="0.001"
                    placeholder="Qtd"
                    {...register(`ficha_tecnica.${idx}.quantidade`)}
                  />
                  {opts.length > 1 ? (
                    <select
                      className="w-20 rounded border px-2 py-1 text-sm"
                      value={selUnit}
                      onChange={(e) =>
                        setSelectedUnits((prev) => {
                          const next = [...prev];
                          next[idx] = e.target.value;
                          return next;
                        })
                      }
                    >
                      {opts.map((o) => (
                        <option key={o.value} value={o.value}>{o.label}</option>
                      ))}
                    </select>
                  ) : (
                    <div className="w-20 py-1 text-sm text-gray-500">{insumo?.unidade_base ?? ""}</div>
                  )}
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      remove(idx);
                      setSelectedUnits((prev) => prev.filter((_, i) => i !== idx));
                    }}
                  >
                    ✕
                  </Button>
                </div>
              );
            })}
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

    <InsumoModal
      open={novoInsumoIdx !== null}
      onClose={() => setNovoInsumoIdx(null)}
      onSuccess={handleInsumoCreated}
    />

    <CategoriaModal
      open={novaCategOpen}
      onClose={() => setNovaCategOpen(false)}
      onCreated={handleCategoriaCreated}
    />
    </>
  );
}
