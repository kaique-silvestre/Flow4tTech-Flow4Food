import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { stockDisplay } from "@/lib/format";
import { baixaSemVendaSchema, motivoPerdaOptions, type BaixaSemVendaFormValues } from "./estoqueSchemas";
import { useBaixaSemVenda, type SaldoItemResponse } from "./useEstoque";

interface Props {
  open: boolean;
  onClose: () => void;
  itens: SaldoItemResponse[];
  preSelectedItemId?: number;
}

export function BaixaSemVendaModal({ open, onClose, itens, preSelectedItemId }: Props) {
  const baixa = useBaixaSemVenda();

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<BaixaSemVendaFormValues>({
    resolver: zodResolver(baixaSemVendaSchema),
    defaultValues: { motivo: "perda" },
  });

  const itemId = watch("item_id");
  const selectedItem = itens.find((i) => i.id === Number(itemId));

  useEffect(() => {
    if (open) {
      reset({
        item_id: preSelectedItemId ?? (undefined as unknown as number),
        motivo: "perda",
        quantidade: undefined as unknown as number,
        observacao: "",
      });
    }
  }, [open, preSelectedItemId, reset]);

  function onSubmit(data: BaixaSemVendaFormValues) {
    baixa.mutate(data, { onSuccess: onClose });
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Baixa Sem Venda</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Item */}
          <div className="space-y-1">
            <Label>Item</Label>
            <select
              className="w-full rounded border px-2 py-1.5 text-sm"
              {...register("item_id", { setValueAs: (v) => Number(v) })}
            >
              <option value={0}>Selecione...</option>
              {itens.map((i) => {
                const { qty, unit } = stockDisplay(i.estoque_atual, i.unidade_base);
                return (
                  <option key={i.id} value={i.id}>
                    {i.nome} ({qty} {unit})
                  </option>
                );
              })}
            </select>
            {errors.item_id && <p className="text-xs text-red-500">{errors.item_id.message}</p>}
          </div>

          {/* Quantidade */}
          <div className="space-y-1">
            <Label htmlFor="quantidade">
              Quantidade {selectedItem ? `(${selectedItem.unidade_base})` : ""}
            </Label>
            <Input id="quantidade" type="number" step="0.001" min="0" {...register("quantidade")} />
            {errors.quantidade && <p className="text-xs text-red-500">{errors.quantidade.message}</p>}
          </div>

          {/* Motivo */}
          <div className="space-y-1">
            <Label>Motivo</Label>
            <div className="space-y-1">
              {motivoPerdaOptions.map((opt) => (
                <label key={opt.value} className="flex cursor-pointer items-center gap-2 text-sm">
                  <input type="radio" value={opt.value} {...register("motivo")} />
                  {opt.label}
                </label>
              ))}
            </div>
            {errors.motivo && <p className="text-xs text-red-500">{errors.motivo.message}</p>}
          </div>

          {/* Observação */}
          <div className="space-y-1">
            <Label htmlFor="observacao">Observação (opcional)</Label>
            <textarea
              id="observacao"
              className="w-full rounded border px-2 py-1.5 text-sm"
              rows={2}
              {...register("observacao")}
            />
          </div>

          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>Cancelar</Button>
            <Button type="submit" disabled={baixa.isPending}>
              {baixa.isPending ? "Confirmando..." : "Confirmar"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
