import { zodResolver } from "@hookform/resolvers/zod";
import { useMemo, useRef, useState } from "react";
import { Controller, useFieldArray, useForm, useWatch } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MoneyInput } from "@/components/ui/money-input";
import { useFornecedores, type Fornecedor } from "@/features/cadastros/fornecedores/useFornecedores";
import { FornecedorModal } from "@/features/cadastros/fornecedores/FornecedorModal";
import { useInsumos, type InsumoResponse } from "@/features/estoque/useInsumos";
import { useCategorias, flattenCategorias } from "@/features/cadastros/categorias/useCategorias";
import type { Categoria } from "@/features/cadastros/categorias/useCategorias";
import { formatCurrency } from "@/lib/format";
import { getFamilyOptions, toBase } from "@/lib/units";
import { compraSchema, type CompraFormValues } from "./compraSchemas";
import { useCreateCompra } from "./useCompras";
import { InsumoModal } from "./InsumoModal";
import { calculateLine, type LastEdited } from "./compraCalculations";

export function NovaCompraPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const createCompra = useCreateCompra();
  const { data: fornecedoresData } = useFornecedores();
  const fornecedores = fornecedoresData?.itens ?? [];
  const { data: insumosData } = useInsumos();
  const itensSimples = insumosData?.itens ?? [];

  const [novoFornOpen, setNovoFornOpen] = useState(false);
  const [insumoModalIndex, setInsumoModalIndex] = useState<number | null>(null);
  const [catFiltroCompra, setCatFiltroCompra] = useState<number | null>(null);
  const { data: categoriasTree = [] } = useCategorias();

  function collectCatIds(id: number, tree: Categoria[]): Set<number> {
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

  const insumosFiltered = catFiltroCompra !== null
    ? itensSimples.filter((i) => i.categoria_id != null && collectCatIds(catFiltroCompra!, categoriasTree).has(i.categoria_id))
    : itensSimples;

  // custo_unitario per row (not in RHF schema — UI only)
  const [unitarios, setUnitarios] = useState<string[]>([""]); // one per row
  const [unitSels, setUnitSels] = useState<string[]>([""]); // selected unit per row
  const lastEditedRef = useRef<Record<number, LastEdited>>({});

  const today = new Date().toISOString().split("T")[0];

  const {
    register,
    handleSubmit,
    control,
    setValue,
    getValues,
    watch,
    formState: { errors },
  } = useForm<CompraFormValues>({
    resolver: zodResolver(compraSchema),
    defaultValues: {
      data_compra: today,
      tipo_compra: "imediata",
      itens: [{ item_id: 0, quantidade: 0, custo_total: 0 }],
    },
  });

  const tipoCompra = watch("tipo_compra");

  const { fields, append, remove } = useFieldArray({ control, name: "itens" });
  const itensWatch = useWatch({ control, name: "itens" });

  const totalCompra = useMemo(() => {
    return (itensWatch ?? []).reduce((sum, i) => sum + Number(i.custo_total || 0), 0);
  }, [itensWatch]);

  function round2(v: number) {
    return Math.round(v * 100) / 100;
  }

  // Returns qty in base unit (g, kg, un, etc.)
  function getBaseQty(index: number, qty: number): number {
    const itemId = getValues(`itens.${index}.item_id`);
    const item = itensSimples.find((i) => i.id === Number(itemId));
    if (!item) return qty;
    const opts = getFamilyOptions(item.unidade_base, item.quantidade_caixa);
    const selVal = unitSels[index] || item.unidade_base;
    const opt = opts.find((o) => o.value === selVal) ?? opts[0];
    return toBase(qty, opt);
  }

  // Price is always shown/entered as R$ per kg for weight items (g or kg base).
  // Returns { unit, factor } where factor converts baseQty → priceQty.
  function getPriceUnitFor(index: number): { unit: string; factor: number } {
    const itemId = getValues(`itens.${index}.item_id`);
    const item = itensSimples.find((i) => i.id === Number(itemId));
    const base = item?.unidade_base ?? "";
    if (base === "g") return { unit: "kg", factor: 0.001 };
    return { unit: base || "un", factor: 1 };
  }

  function handleUnitarioChange(index: number, raw: string) {
    lastEditedRef.current[index] = "unitario";
    setUnitarios((prev) => {
      const next = [...prev];
      next[index] = raw;
      return next;
    });
    const unitario = parseFloat(raw) || 0;
    const qty = parseFloat(String(getValues(`itens.${index}.quantidade`))) || 0;
    const baseQty = getBaseQty(index, qty);
    const { factor } = getPriceUnitFor(index);
    const priceQty = baseQty * factor;
    if (priceQty > 0 && unitario > 0) {
      setValue(`itens.${index}.custo_total`, round2(unitario * priceQty) as never);
    }
  }

  function handleTotalChange(index: number, total: number) {
    lastEditedRef.current[index] = "total";
    const qty = parseFloat(String(getValues(`itens.${index}.quantidade`))) || 0;
    const baseQty = getBaseQty(index, qty);
    const { factor } = getPriceUnitFor(index);
    const priceQty = baseQty * factor;
    if (priceQty > 0 && total > 0) {
      setUnitarios((prev) => {
        const next = [...prev];
        next[index] = String(round2(total / priceQty));
        return next;
      });
    }
  }

  function handleQtdChange(index: number, raw: string) {
    const qty = parseFloat(raw) || 0;
    const baseQty = getBaseQty(index, qty);
    const { factor } = getPriceUnitFor(index);
    const priceQty = baseQty * factor;
    const mode = lastEditedRef.current[index] ?? "unitario";
    const result = calculateLine({
      quantidade: priceQty,
      custo_unitario: parseFloat(unitarios[index] ?? "") || 0,
      custo_total: parseFloat(String(getValues(`itens.${index}.custo_total`))) || 0,
      lastEdited: mode,
    });
    if (mode === "unitario" && result.custo_total > 0) {
      setValue(`itens.${index}.custo_total`, result.custo_total as never);
    } else if (mode === "total" && result.custo_unitario > 0) {
      setUnitarios((prev) => {
        const next = [...prev];
        next[index] = String(result.custo_unitario);
        return next;
      });
    }
  }

  function handleFornecedorCreated(forn: Fornecedor) {
    qc.setQueryData<Fornecedor[]>(["fornecedores"], (old = []) =>
      old.some((f) => f.id === forn.id) ? old : [...old, forn]
    );
    setValue("fornecedor_id", forn.id as never);
  }

  function handleInsumoCreated(insumo: InsumoResponse) {
    if (insumoModalIndex !== null) {
      const currentItemId = Number(getValues(`itens.${insumoModalIndex}.item_id`));
      if (currentItemId !== 0) {
        // Row already has an insumo — append a new row below
        append({ item_id: insumo.id, quantidade: 0, custo_total: 0 });
        setUnitarios((prev) => [...prev, ""]);
        setUnitSels((prev) => [...prev, insumo.unidade_base]);
      } else {
        // Empty row — fill it
        setValue(`itens.${insumoModalIndex}.item_id`, insumo.id);
        handleItemChange(insumoModalIndex, insumo);
      }
    }
    setInsumoModalIndex(null);
  }

  function handleAppend() {
    append({ item_id: 0, quantidade: 0, custo_total: 0 });
    setUnitarios((prev) => [...prev, ""]);
    setUnitSels((prev) => [...prev, ""]);
  }

  function handleItemChange(index: number, item?: InsumoResponse) {
    setValue(`itens.${index}.quantidade`, 0 as never);
    setValue(`itens.${index}.custo_total`, 0 as never);
    setUnitarios((prev) => {
      const next = [...prev];
      next[index] = "";
      return next;
    });
    setUnitSels((prev) => {
      const next = [...prev];
      next[index] = item?.unidade_base ?? "";
      return next;
    });
    delete lastEditedRef.current[index];
  }

  function handleRemove(index: number) {
    remove(index);
    setUnitarios((prev) => prev.filter((_, i) => i !== index));
    setUnitSels((prev) => prev.filter((_, i) => i !== index));
    const newLastEdited: Record<number, LastEdited> = {};
    Object.entries(lastEditedRef.current).forEach(([k, v]) => {
      const ki = parseInt(k);
      if (ki < index) newLastEdited[ki] = v;
      else if (ki > index) newLastEdited[ki - 1] = v;
    });
    lastEditedRef.current = newLastEdited;
  }

  function onSubmit(data: CompraFormValues) {
    const converted: CompraFormValues = {
      ...data,
      // strip empty strings so backend doesn't receive "" as a date
      data_prevista_recebimento: data.data_prevista_recebimento || undefined,
      data_prevista_pagamento: data.data_prevista_pagamento || undefined,
      itens: data.itens.map((row, index) => {
        const itemId = row.item_id;
        const item = itensSimples.find((i) => i.id === Number(itemId));
        if (!item) return row;
        const options = getFamilyOptions(item.unidade_base, item.quantidade_caixa);
        const selVal = unitSels[index] || item.unidade_base;
        const opt = options.find((o) => o.value === selVal) ?? options[0];
        return { ...row, quantidade: toBase(Number(row.quantidade), opt) };
      }),
    };
    createCompra.mutate(converted);
  }

  return (
    <div className="p-6 max-w-4xl">
      <div className="mb-6 flex items-center gap-4">
        <Button variant="outline" size="sm" onClick={() => navigate("/compras")}>← Voltar</Button>
        <h1 className="text-xl font-semibold">Nova Compra</h1>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* Fornecedor */}
        <div className="space-y-1">
          <Label>Fornecedor</Label>
          <select
            className="w-full rounded border px-2 py-1.5 text-sm"
            {...register("fornecedor_id", { setValueAs: (v) => (v === "" ? undefined : Number(v)) })}
          >
            <option value="">Selecione...</option>
            {fornecedores.map((f) => (
              <option key={f.id} value={f.id}>{f.nome}</option>
            ))}
          </select>
          <button
            type="button"
            className="text-xs text-blue-600 hover:underline mt-0.5"
            onClick={() => setNovoFornOpen(true)}
          >
            [ + Cadastrar novo fornecedor ]
          </button>
        </div>

        {/* Tipo de compra */}
        <div className="space-y-1">
          <Label>Tipo de compra</Label>
          <div className="flex gap-2">
            {[
              { value: "imediata", label: "Imediata", desc: "Recebe e paga agora" },
              { value: "agendada", label: "Agendada", desc: "Recebe depois, paga depois" },
              { value: "a_prazo", label: "A prazo", desc: "Recebe agora, paga depois" },
            ].map((opt) => (
              <label
                key={opt.value}
                className={`flex-1 cursor-pointer rounded border p-2 text-sm transition-colors ${
                  tipoCompra === opt.value ? "border-gray-800 bg-gray-50" : "border-gray-200 hover:bg-gray-50"
                }`}
              >
                <input type="radio" className="sr-only" value={opt.value} {...register("tipo_compra")} />
                <div className="font-medium">{opt.label}</div>
                <div className="text-xs text-gray-400">{opt.desc}</div>
              </label>
            ))}
          </div>
        </div>

        {/* Data + Nota */}
        <div className="flex gap-4">
          <div className="flex-1 space-y-1">
            <Label htmlFor="data_compra">Data da compra</Label>
            <Input id="data_compra" type="date" {...register("data_compra")} />
            {errors.data_compra && <p className="text-xs text-red-500">{errors.data_compra.message}</p>}
          </div>
          <div className="flex-1 space-y-1">
            <Label htmlFor="numero_nota">Número da nota</Label>
            <Input id="numero_nota" placeholder="Opcional" {...register("numero_nota")} />
          </div>
        </div>

        {/* Datas condicionais */}
        {(tipoCompra === "agendada" || tipoCompra === "a_prazo") && (
          <div className="flex gap-4">
            {tipoCompra === "agendada" && (
              <div className="flex-1 space-y-1">
                <Label htmlFor="data_prevista_recebimento">Data prevista de recebimento *</Label>
                <Input id="data_prevista_recebimento" type="date" {...register("data_prevista_recebimento")} />
                {errors.data_prevista_recebimento && (
                  <p className="text-xs text-red-500">{errors.data_prevista_recebimento.message}</p>
                )}
              </div>
            )}
            <div className="flex-1 space-y-1">
              <Label htmlFor="data_prevista_pagamento">Vencimento do pagamento *</Label>
              <Input id="data_prevista_pagamento" type="date" {...register("data_prevista_pagamento")} />
              {errors.data_prevista_pagamento && (
                <p className="text-xs text-red-500">{errors.data_prevista_pagamento.message}</p>
              )}
            </div>
          </div>
        )}

        {/* Itens */}
        <div className="space-y-2 rounded border p-3">
          <div className="flex items-center justify-between mb-1">
            <Label className="font-semibold">Itens comprados</Label>
            <div className="flex items-center gap-2">
              <select
                value={catFiltroCompra ?? ""}
                onChange={(e) => setCatFiltroCompra(e.target.value ? Number(e.target.value) : null)}
                className="rounded border px-2 py-1 text-xs text-gray-700"
              >
                <option value="">Todas as categorias</option>
                {flattenCategorias(categoriasTree).map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.indent ? `  ${c.nome}` : c.nome}
                  </option>
                ))}
              </select>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={handleAppend}
              >
                + Adicionar item
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-[1fr_90px_110px_100px_110px_32px] gap-2 text-xs text-gray-500 px-1">
            <span>Item</span>
            <span>Quantidade</span>
            <span>Unidade</span>
            <span>Preço/unid. base</span>
            <span>Total (R$)</span>
            <span />
          </div>

          {fields.map((field, index) => {
            const itemId = itensWatch?.[index]?.item_id;
            const item = itensSimples.find((i) => i.id === Number(itemId));
            const familyOpts = item ? getFamilyOptions(item.unidade_base, item.quantidade_caixa) : [];
            const selUnit = unitSels[index] || item?.unidade_base || "";

            return (
              <div key={field.id} className="grid grid-cols-[1fr_90px_110px_100px_110px_32px] gap-2 items-start">
                {/* Item selector */}
                <div>
                  <Controller
                    control={control}
                    name={`itens.${index}.item_id`}
                    render={({ field }) => (
                      <select
                        className="w-full rounded border px-2 py-1.5 text-sm"
                        value={field.value || 0}
                        onChange={(e) => {
                          const newVal = Number(e.target.value);
                          field.onChange(newVal);
                          const found = itensSimples.find((i) => i.id === newVal);
                          handleItemChange(index, found);
                        }}
                        onBlur={field.onBlur}
                        ref={field.ref}
                      >
                        <option value={0}>Selecione...</option>
                        {insumosFiltered.map((i) => (
                          <option key={i.id} value={i.id}>{i.nome}</option>
                        ))}
                      </select>
                    )}
                  />
                  {errors.itens?.[index]?.item_id && (
                    <p className="text-xs text-red-500">{errors.itens[index]?.item_id?.message}</p>
                  )}
                  {index === fields.length - 1 && (
                    <button
                      type="button"
                      className="text-xs text-blue-600 hover:underline mt-0.5"
                      onClick={() => setInsumoModalIndex(index)}
                    >
                      [ + Cadastrar novo insumo ]
                    </button>
                  )}
                </div>

                {/* Quantidade */}
                <div>
                  <Input
                    type="number"
                    step="0.001"
                    min="0"
                    placeholder={selUnit ? `0.000 ${selUnit}` : "0.000"}
                    {...register(`itens.${index}.quantidade`, {
                      onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
                        handleQtdChange(index, e.target.value),
                    })}
                  />
                  {errors.itens?.[index]?.quantidade && (
                    <p className="text-xs text-red-500">{errors.itens[index]?.quantidade?.message}</p>
                  )}
                </div>

                {/* Unidade */}
                <div>
                  {familyOpts.length > 1 ? (
                    <select
                      className="w-full rounded border px-2 py-1.5 text-sm"
                      value={selUnit}
                      onChange={(e) => {
                        const newUnit = e.target.value;
                        setUnitSels((prev) => {
                          const next = [...prev];
                          next[index] = newUnit;
                          return next;
                        });
                        setValue(`itens.${index}.quantidade`, 0 as never);
                        setValue(`itens.${index}.custo_total`, 0 as never);
                        setUnitarios((prev) => {
                          const next = [...prev];
                          next[index] = "";
                          return next;
                        });
                        delete lastEditedRef.current[index];
                      }}
                    >
                      {familyOpts.map((o) => (
                        <option key={o.value} value={o.value}>{o.label}</option>
                      ))}
                    </select>
                  ) : (
                    <div className="py-1.5 text-sm text-gray-500">{item?.unidade_base ?? "—"}</div>
                  )}
                </div>

                {/* Custo Unitário — UI only, not in RHF — R$/kg for weight items */}
                <div>
                  <MoneyInput
                    value={unitarios[index] ?? ""}
                    onValueChange={(raw) => handleUnitarioChange(index, raw)}
                  />
                  {item && (
                    <p className="text-xs text-gray-400 mt-0.5">
                      R$ por {getPriceUnitFor(index).unit}
                    </p>
                  )}
                </div>

                {/* Custo Total */}
                <div>
                  <Controller
                    name={`itens.${index}.custo_total`}
                    control={control}
                    render={({ field }) => (
                      <MoneyInput
                        value={field.value || ""}
                        onValueChange={(raw) => {
                          const total = parseFloat(raw) || 0;
                          field.onChange(total);
                          handleTotalChange(index, total);
                        }}
                      />
                    )}
                  />
                  {errors.itens?.[index]?.custo_total && (
                    <p className="text-xs text-red-500">{errors.itens[index]?.custo_total?.message}</p>
                  )}
                </div>

                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="text-red-500 hover:text-red-700 px-2"
                  onClick={() => handleRemove(index)}
                  disabled={fields.length === 1}
                >
                  ✕
                </Button>
              </div>
            );
          })}

          {errors.itens?.root && (
            <p className="text-sm text-red-500">{errors.itens.root.message}</p>
          )}
          {errors.itens?.message && (
            <p className="text-sm text-red-500">{errors.itens.message}</p>
          )}
        </div>

        {/* Total */}
        <div className="text-right text-sm">
          Total da compra: <span className="font-semibold text-base">{formatCurrency(totalCompra)}</span>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={() => navigate("/compras")}>
            Cancelar
          </Button>
          <Button type="submit" disabled={createCompra.isPending}>
            {createCompra.isPending ? "Salvando..." : "Salvar Compra"}
          </Button>
        </div>
      </form>

      <InsumoModal
        open={insumoModalIndex !== null}
        onClose={() => setInsumoModalIndex(null)}
        onSuccess={handleInsumoCreated}
      />
      <FornecedorModal
        open={novoFornOpen}
        onClose={() => setNovoFornOpen(false)}
        onCreated={handleFornecedorCreated}
      />
    </div>
  );
}
