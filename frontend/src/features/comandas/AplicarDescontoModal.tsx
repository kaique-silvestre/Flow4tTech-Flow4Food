import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { aplicarDescontoSchema, type AplicarDescontoValues } from "./fechamentoSchemas";
import { useAplicarDesconto } from "./useFechamento";
import type { ComandaResponse } from "./useComandas";

interface Props {
  open: boolean;
  onClose: () => void;
  comanda: ComandaResponse;
}

export default function AplicarDescontoModal({ open, onClose, comanda }: Props) {
  const { mutate, isPending } = useAplicarDesconto(comanda.id);
  const { register, handleSubmit, watch, control, formState: { errors } } = useForm<AplicarDescontoValues>({
    resolver: zodResolver(aplicarDescontoSchema),
    defaultValues: {
      tipo: comanda.desconto_percentual ? "percentual" : "valor",
      valor: comanda.desconto_percentual ?? comanda.desconto_valor ?? undefined,
    },
  });

  const tipo = watch("tipo");

  function onSubmit(data: AplicarDescontoValues) {
    mutate(data, { onSuccess: onClose });
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Aplicar Desconto</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Controller
            control={control}
            name="tipo"
            render={({ field }) => (
              <div className="flex gap-4">
                {(["percentual", "valor"] as const).map((t) => (
                  <div key={t} className="flex items-center gap-2">
                    <input
                      type="radio"
                      id={`desc-${t}`}
                      value={t}
                      checked={field.value === t}
                      onChange={() => field.onChange(t)}
                      className="h-4 w-4 accent-blue-600"
                    />
                    <Label htmlFor={`desc-${t}`}>
                      {t === "percentual" ? "Percentual (%)" : "Valor fixo (R$)"}
                    </Label>
                  </div>
                ))}
              </div>
            )}
          />
          <div>
            <Label>{tipo === "percentual" ? "Desconto %" : "Desconto R$"}</Label>
            <Input
              type="number"
              step="0.01"
              min="0"
              max={tipo === "percentual" ? "100" : undefined}
              {...register("valor")}
              className="mt-1"
            />
            {errors.valor && <p className="text-sm text-destructive mt-1">{errors.valor.message}</p>}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>Cancelar</Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? "Aplicando..." : "Aplicar Desconto"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
