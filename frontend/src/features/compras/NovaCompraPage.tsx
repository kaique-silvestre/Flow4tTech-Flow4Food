import { zodResolver } from "@hookform/resolvers/zod";
import { useMemo, useRef, useState } from "react";
import { useFieldArray, useForm, useWatch } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useFornecedores, useCreateFornecedor } from "@/features/cadastros/fornecedores/useFornecedores";
import { useInsumos, type InsumoResponse } from "@/features/estoque/useInsumos";
import { formatCurrency } from "@/lib/format";
import { getFamilyOptions, toBase } from "@/lib/units";
import { compraSchema, type CompraFormValues } from "./compraSchemas";
import { useCreateCompra } from "./useCompras";
import { InsumoModal } from "./InsumoModal";
import { calculateLine, type LastEdited } from "./compraCalculations";

export function NovaCompraPage() {
  const navigate = useNavigate();
  const createCompra = useCreateCompra();
  const { data: fornecedores = [], refetch: refetchFornecedores } = useFornecedores();
  const { data: itensSimples = [] } = useInsumos();
  const createFornecedor = useCreateFornecedor();

  const [novoFornNome, setNovoFornNome] = useState("");
  const [showNovoForn, setShowNovoForn] = useState(false);
  const [insumoModalIndex, setInsumoModalIndex] = useState<number | null>(null);

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
    formState: { errors },
  } = useForm<CompraFormValues>({
    resolver: zodResolver(compraSchema),
    defaultValues: {
      data_compra: today,
      itens: [{ item_id: 0, quantidade: 0, custo_total: 0 }],
    },
  });

  const { fields, append, remove } = useFieldArray({ control, name: "itens" });
  const itensWatch = useWatch({ control, name: "itens" });

  const totalCompra = useMemo(() => {
    return (itensWatch ?? []).reduce((sum, i) => sum + Number(i.custo_total || 0), 0);
  }, [itensWatch]);

  function round2(v: number) {
    return Math.round(v * 100) / 100;
  }

  // Returns qty converted to the insumo's base unit for cost calculations.
  // custo_unitario is always R$ per base unit.
  function getBaseQty(index: number, qty: number): number {
    const itemId = getValues(`itens.${index}.item_id`);
    const item = itensSimples.find((i) => i.id === Number(itemId));
    if (!item) return qty;
    const opts = getFamilyOptions(item.unidade_base, item.quantidade_caixa);
    const selVal = unitSels[index] || item.unidade_base;
    const opt = opts.find((o) => o.value === selVal) ?? opts[0];
    return toBase(qty, opt);
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
    if (baseQty > 0 && unitario > 0) {
      setValue(`itens.${index}.custo_total`, round2(unitario * baseQty) as never);
    }
  }

  function handleTotalChange(index: number, rawEvent: React.ChangeEvent<HTMLInputElement>) {
    lastEditedRef.current[index] = "total";
    const total = parseFloat(rawEvent.target.value) || 0;
    const qty = parseFloat(String(getValues(`itens.${index}.quantidade`))) || 0;
    const baseQty = getBaseQty(index, qty);
    if (baseQty > 0 && total > 0) {
      setUnitarios((prev) => {
        const next = [...prev];
        next[index] = String(round2(total / baseQty));
        return next;
      });
    }
  }

  function handleQtdChange(index: number, raw: string) {
    const qty = parseFloat(raw) || 0;
    const baseQty = getBaseQty(index, qty);
    const mode = lastEditedRef.current[index] ?? "unitario";
    const result = calculateLine({
      quantidade: baseQty,
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

  function handleAddFornecedor() {
    if (!novoFornNome.trim()) return;
    createFornecedor.mutate(
      { nome: novoFornNome.trim(), telefone: null, email: null },
      {
        onSuccess: () => {
          refetchFornecedores();
          setNovoFornNome("");
          setShowNovoForn(false);
        },
      }
    );
  }

  function handleInsumoCreated(insumo: InsumoResponse) {
    if (insumoModalIndex !== null) {
      setValue(`itens.${insumoModalIndex}.item_id`, insumo.id);
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
          {!showNovoForn ? (
            <button
              type="button"
              className="text-xs text-blue-600 hover:underline"
              onClick={() => setShowNovoForn(true)}
            >
              + Cadastrar novo fornecedor
            </button>
          ) : (
            <div className="flex gap-2 items-center">
              <Input
                className="text-sm"
                placeholder="Nome do fornecedor"
                value={novoFornNome}
                onChange={(e) => setNovoFornNome(e.target.value)}
              />
              <Button type="button" size="sm" onClick={handleAddFornecedor} disabled={createFornecedor.isPending}>
                Salvar
              </Button>
              <Button type="button" size="sm" variant="outline" onClick={() => setShowNovoForn(false)}>
                Cancelar
              </Button>
            </div>
          )}
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

        {/* Itens */}
        <div className="space-y-2 rounded border p-3">
          <div className="flex items-center justify-between mb-1">
            <Label className="font-semibold">Itens comprados</Label>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={handleAppend}
            >
              + Adicionar item
            </Button>
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
                  <select
                    className="w-full rounded border px-2 py-1.5 text-sm"
                    {...register(`itens.${index}.item_id`, {
                      setValueAs: (v) => Number(v),
                      onChange: (e: React.ChangeEvent<HTMLSelectElement>) => {
                        const found = itensSimples.find((i) => i.id === Number(e.target.value));
                        handleItemChange(index, found);
                      },
                    })}
                  >
                    <option value={0}>Selecione...</option>
                    {itensSimples.map((i) => (
                      <option key={i.id} value={i.id}>{i.nome}</option>
                    ))}
                  </select>
                  {errors.itens?.[index]?.item_id && (
                    <p className="text-xs text-red-500">{errors.itens[index]?.item_id?.message}</p>
                  )}
                  <button
                    type="button"
                    className="text-xs text-blue-600 hover:underline mt-0.5"
                    onClick={() => setInsumoModalIndex(index)}
                  >
                    [ + Cadastrar novo insumo ]
                  </button>
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

                {/* Custo Unitário — UI only, not in RHF — always R$ per base unit */}
                <div>
                  <Input
                    type="number"
                    step="0.0001"
                    min="0"
                    value={unitarios[index] ?? ""}
                    onChange={(e) => handleUnitarioChange(index, e.target.value)}
                    placeholder="0.00"
                  />
                  {item && (
                    <p className="text-xs text-gray-400 mt-0.5">R$ por {item.unidade_base}</p>
                  )}
                </div>

                {/* Custo Total */}
                <div>
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    {...register(`itens.${index}.custo_total`, {
                      onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
                        handleTotalChange(index, e),
                    })}
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
    </div>
  );
}
