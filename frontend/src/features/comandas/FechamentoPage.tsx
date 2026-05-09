import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useForm, useFieldArray, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { formatCurrency } from "@/lib/format";
import { useComanda } from "./useComandas";
import { useFecharComanda, useMetodosPagamento } from "./useFechamento";
import { fecharComandaSchema, type FecharComandaValues } from "./fechamentoSchemas";
import AplicarDescontoModal from "./AplicarDescontoModal";

export default function FechamentoPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: comanda, isLoading } = useComanda(id!);
  const { data: metodos } = useMetodosPagamento();
  const { mutate: fechar, isPending } = useFecharComanda(id!);
  const [descontoOpen, setDescontoOpen] = useState(false);
  const [nPessoas, setNPessoas] = useState<number | "">(2);

  const { register, control, handleSubmit, watch, setValue, formState: { errors, isSubmitted } } = useForm<FecharComandaValues>({
    resolver: zodResolver(fecharComandaSchema),
    defaultValues: {
      pagamentos: [{ metodo_id: 0, valor: 0 }],
      modo_divisao: "sem_divisao",
    },
  });

  const { fields, append, remove } = useFieldArray({ control, name: "pagamentos" });
  const modo = watch("modo_divisao");
  const pagamentos = watch("pagamentos");
  const pagamentosWatched = useWatch({ control, name: "pagamentos" });
  const hasInvalidMethod = pagamentosWatched.some((p) => !p.metodo_id);

  useEffect(() => {
    if (comanda) {
      const sub = comanda.total_parcial;
      const desc = comanda.desconto_percentual
        ? sub * (comanda.desconto_percentual / 100)
        : (comanda.desconto_valor ?? 0);
      const base = comanda.saldo_pendente ?? (sub - desc);
      setValue("pagamentos.0.valor", Number(base.toFixed(2)));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [comanda?.id]);

  if (isLoading || !comanda) {
    return (
      <div className="p-6 space-y-4">
        <div className="h-8 w-64 bg-gray-200 animate-pulse rounded" />
        <div className="h-48 w-full bg-gray-200 animate-pulse rounded" />
      </div>
    );
  }

  const subtotal = comanda.total_parcial;
  const desconto = comanda.desconto_percentual
    ? subtotal * (comanda.desconto_percentual / 100)
    : (comanda.desconto_valor ?? 0);
  const totalComDesconto = subtotal - desconto;
  const baseTotal = comanda.saldo_pendente ?? totalComDesconto;
  const totalPago = pagamentos.reduce((s, p) => s + (Number(p.valor) || 0), 0);
  const bate = Math.abs(totalPago - baseTotal) <= 0.01;

  function onSubmit(data: FecharComandaValues) {
    fechar(data);
  }

  const itensNaoCancelados = comanda.itens_ativos.filter((i) => !i.cancelado);

  const modoOpcoes: { value: FecharComandaValues["modo_divisao"]; label: string }[] = [
    { value: "sem_divisao", label: "Sem divisão (paga tudo)" },
    { value: "igualmente", label: "Dividir igualmente entre N pessoas" },
    { value: "por_pessoa", label: "Cada pessoa paga um valor diferente" },
    { value: "parcial", label: "Pagamento parcial (comanda continua aberta)" },
  ];

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="sm" onClick={() => navigate(`/comandas/${id}`)}>
          ← Voltar
        </Button>
        <h1 className="text-xl font-bold">
          Fechar Comanda #{comanda.id} — {comanda.identificacao}
        </h1>
      </div>

      {/* Resumo */}
      <div className="border rounded-lg p-4 space-y-2">
        <h2 className="font-semibold text-lg mb-3">Resumo</h2>
        {itensNaoCancelados.map((item) => (
          <div key={item.id} className="flex justify-between text-sm">
            <span>
              {item.quantidade}× {item.item_nome}
              {item.cortesia && " 🎁"}
              {item.pessoa_associada && ` (${item.pessoa_associada})`}
            </span>
            <span>{formatCurrency(item.subtotal)}</span>
          </div>
        ))}
        <div className="border-t pt-2 mt-2 space-y-1">
          <div className="flex justify-between text-sm">
            <span>Subtotal</span>
            <span>{formatCurrency(subtotal)}</span>
          </div>
          {desconto > 0 && (
            <div className="flex justify-between text-sm text-green-600">
              <span>Desconto{comanda.desconto_percentual ? ` (${comanda.desconto_percentual}%)` : ""}</span>
              <span>-{formatCurrency(desconto)}</span>
            </div>
          )}
          <div className="flex justify-between font-bold">
            <span>TOTAL</span>
            <span>{formatCurrency(comanda.saldo_pendente ?? totalComDesconto)}</span>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={() => setDescontoOpen(true)}>
          {desconto > 0 ? "Editar Desconto" : "Aplicar Desconto"}
        </Button>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Modo de divisão */}
        <div>
          <Label className="text-base font-semibold">Como dividir?</Label>
          <div className="mt-2 space-y-2">
            {modoOpcoes.map((opt) => (
              <div key={opt.value} className="flex items-center gap-2">
                <input
                  type="radio"
                  id={`modo-${opt.value}`}
                  name="modo_divisao"
                  value={opt.value}
                  checked={modo === opt.value}
                  onChange={() => {
                    setValue("modo_divisao", opt.value);
                    if (opt.value === "sem_divisao") {
                      setValue("pagamentos.0.valor", Number(baseTotal.toFixed(2)));
                    } else {
                      setValue("pagamentos.0.valor", 0);
                    }
                  }}
                  className="h-4 w-4 accent-blue-600"
                />
                <Label htmlFor={`modo-${opt.value}`}>{opt.label}</Label>
              </div>
            ))}
          </div>
        </div>

        {/* Divisão por N pessoas */}
        {modo === "igualmente" && (
          <div className="border rounded-lg p-4 space-y-3 bg-blue-50">
            <Label className="text-sm font-semibold">Divisão igualitária</Label>
            <div className="flex items-center gap-3">
              <Label className="text-sm whitespace-nowrap">Nº de pessoas:</Label>
              <Input
                type="number"
                min={2}
                step={1}
                className="w-24"
                value={nPessoas}
                onChange={(e) => setNPessoas(e.target.value === "" ? "" : Math.max(2, parseInt(e.target.value, 10)))}
              />
            </div>
            {nPessoas !== "" && nPessoas >= 2 && (
              <div className="text-sm space-y-1">
                {(() => {
                  const n = nPessoas;
                  const valorBase = Math.floor((baseTotal * 100) / n) / 100;
                  const ultimo = Number((baseTotal - valorBase * (n - 1)).toFixed(2));
                  return (
                    <>
                      <div className="flex justify-between">
                        <span className="text-gray-600">{n - 1} pessoas pagam:</span>
                        <span className="font-medium">{formatCurrency(valorBase)} cada</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">1ª pessoa paga:</span>
                        <span className="font-medium">{formatCurrency(ultimo)}</span>
                      </div>
                      <div className="flex justify-between border-t pt-1 font-semibold">
                        <span>Total:</span>
                        <span>{formatCurrency(baseTotal)}</span>
                      </div>
                    </>
                  );
                })()}
              </div>
            )}
          </div>
        )}

        {/* Pagamentos */}
        <div className="space-y-3">
          <Label className="text-base font-semibold">Pagamento</Label>
          {fields.map((field, idx) => (
            <div key={field.id} className="flex gap-2 items-end">
              <div className="flex-1">
                <Label className="text-xs">Método</Label>
                <select
                  className={`mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring ${isSubmitted && !pagamentos[idx]?.metodo_id ? "border-destructive" : "border-input"}`}
                  value={pagamentos[idx]?.metodo_id || ""}
                  onChange={(e) => setValue(`pagamentos.${idx}.metodo_id`, Number(e.target.value), { shouldDirty: true, shouldTouch: true })}
                >
                  <option value="">Selecione...</option>
                  {metodos?.filter((m) => m.ativo).map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.nome}
                    </option>
                  ))}
                </select>
                {isSubmitted && !pagamentos[idx]?.metodo_id && (
                  <p className="text-xs text-destructive mt-1">Selecione um método</p>
                )}
              </div>
              <div className="w-32">
                <Label className="text-xs">Valor (R$)</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0.01"
                  {...register(`pagamentos.${idx}.valor`, { valueAsNumber: true })}
                />
              </div>
              {fields.length > 1 && (
                <Button type="button" variant="ghost" size="sm" onClick={() => remove(idx)}>
                  ✕
                </Button>
              )}
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => append({ metodo_id: 0, valor: 0 })}
          >
            + Adicionar método de pagamento
          </Button>
          {errors.pagamentos && (
            <p className="text-sm text-destructive">{errors.pagamentos.message}</p>
          )}
        </div>

        {/* Rodapé total */}
        <div className={`flex justify-between font-semibold text-lg border-t pt-3 ${bate ? "text-green-600" : "text-red-500"}`}>
          <span>Total recebido:</span>
          <span>{formatCurrency(totalPago)} {bate && modo !== "parcial" ? "✓" : ""}</span>
        </div>
        {!bate && modo !== "parcial" && (
          <p className="text-sm text-destructive">
            Diferença: {formatCurrency(Math.abs(totalPago - baseTotal))} (faltam{" "}
            {formatCurrency(baseTotal - totalPago)})
          </p>
        )}

        <div className="flex gap-3 justify-end">
          <Button type="button" variant="outline" onClick={() => navigate(`/comandas/${id}`)}>
            Cancelar
          </Button>
          <Button
            type="submit"
            disabled={isPending || hasInvalidMethod || (!bate && modo !== "parcial")}
            className="min-w-[160px]"
          >
            {isPending
              ? "Processando..."
              : modo === "parcial"
              ? "Registrar Pagamento Parcial"
              : "Confirmar Fechamento"}
          </Button>
        </div>
      </form>

      {descontoOpen && (
        <AplicarDescontoModal
          open={descontoOpen}
          onClose={() => setDescontoOpen(false)}
          comanda={comanda}
        />
      )}
    </div>
  );
}
