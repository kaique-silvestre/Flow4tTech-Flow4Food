import { zodResolver } from "@hookform/resolvers/zod";
import { useMemo, useState } from "react";
import { useFieldArray, useForm, useWatch } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useFornecedores, useCreateFornecedor } from "@/features/cadastros/fornecedores/useFornecedores";
import { useItensSimples } from "@/features/cadastros/itens/useItens";
import { formatCurrency } from "@/lib/format";
import { compraSchema, type CompraFormValues } from "./compraSchemas";
import { useCreateCompra } from "./useCompras";

export function NovaCompraPage() {
  const navigate = useNavigate();
  const createCompra = useCreateCompra();
  const { data: fornecedores = [], refetch: refetchFornecedores } = useFornecedores();
  const { data: itensSimples = [] } = useItensSimples();
  const createFornecedor = useCreateFornecedor();

  const [novoFornNome, setNovoFornNome] = useState("");
  const [showNovoForn, setShowNovoForn] = useState(false);

  const today = new Date().toISOString().split("T")[0];

  const {
    register,
    handleSubmit,
    control,
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

  function onSubmit(data: CompraFormValues) {
    createCompra.mutate(data);
  }

  return (
    <div className="p-6 max-w-3xl">
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
              onClick={() => append({ item_id: 0, quantidade: 0, custo_total: 0 })}
            >
              + Adicionar item
            </Button>
          </div>

          <div className="grid grid-cols-[1fr_100px_80px_110px_32px] gap-2 text-xs text-gray-500 px-1">
            <span>Item</span>
            <span>Qtd</span>
            <span>Unidade</span>
            <span>Custo Total (R$)</span>
            <span />
          </div>

          {fields.map((field, index) => {
            const itemId = itensWatch?.[index]?.item_id;
            const item = itensSimples.find((i) => i.id === Number(itemId));
            const qtd = Number(itensWatch?.[index]?.quantidade || 0);
            const custoTotal = Number(itensWatch?.[index]?.custo_total || 0);
            const custoUnitario = qtd > 0 ? custoTotal / qtd : 0;

            return (
              <div key={field.id} className="grid grid-cols-[1fr_100px_80px_110px_32px] gap-2 items-start">
                <div>
                  <select
                    className="w-full rounded border px-2 py-1.5 text-sm"
                    {...register(`itens.${index}.item_id`, { setValueAs: (v) => Number(v) })}
                  >
                    <option value={0}>Selecione...</option>
                    {itensSimples.map((i) => (
                      <option key={i.id} value={i.id}>{i.nome}</option>
                    ))}
                  </select>
                  {errors.itens?.[index]?.item_id && (
                    <p className="text-xs text-red-500">{errors.itens[index]?.item_id?.message}</p>
                  )}
                </div>
                <div>
                  <Input type="number" step="0.001" min="0" {...register(`itens.${index}.quantidade`)} />
                  {errors.itens?.[index]?.quantidade && (
                    <p className="text-xs text-red-500">{errors.itens[index]?.quantidade?.message}</p>
                  )}
                </div>
                <div className="py-1.5 text-sm text-gray-500">{item?.unidade_base ?? "—"}</div>
                <div>
                  <Input type="number" step="0.01" min="0" {...register(`itens.${index}.custo_total`)} />
                  {errors.itens?.[index]?.custo_total && (
                    <p className="text-xs text-red-500">{errors.itens[index]?.custo_total?.message}</p>
                  )}
                  {qtd > 0 && custoTotal > 0 && (
                    <p className="text-xs text-gray-400">{formatCurrency(custoUnitario)}/un</p>
                  )}
                </div>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="text-red-500 hover:text-red-700 px-2"
                  onClick={() => remove(index)}
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
    </div>
  );
}
