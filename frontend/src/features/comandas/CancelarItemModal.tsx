import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { cancelarItemSchema, type CancelarItemValues } from "./comandaSchemas";
import { useCancelarItem } from "./useComandas";

const MOTIVOS = [
  { value: "cliente_desistiu", label: "Cliente desistiu" },
  { value: "erro_lancamento", label: "Erro de lançamento" },
  { value: "item_indisponivel", label: "Item indisponível" },
  { value: "outro", label: "Outro" },
] as const;

interface Props {
  comanda_id: number;
  item_id: number;
  version: number;
  onClose: () => void;
  onSuccess: (data: unknown) => void;
}

export function CancelarItemModal({ comanda_id, item_id, version, onClose, onSuccess }: Props) {
  const cancelar = useCancelarItem(comanda_id);
  const { register, handleSubmit } = useForm<CancelarItemValues>({
    resolver: zodResolver(cancelarItemSchema),
    defaultValues: { motivo: "erro_lancamento", estornado: false },
  });

  function onSubmit(values: CancelarItemValues) {
    cancelar.mutate(
      { ...values, item_id, version },
      { onSuccess: (data) => { onSuccess(data); onClose(); } },
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">Cancelar Item</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label htmlFor="motivo">Motivo</Label>
            <select
              id="motivo"
              className="mt-1 w-full rounded border px-3 py-2 text-sm"
              {...register("motivo")}
            >
              {MOTIVOS.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <input type="checkbox" id="estornado" {...register("estornado")} />
            <Label htmlFor="estornado">Estornar itens ao estoque</Label>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Voltar
            </Button>
            <Button type="submit" disabled={cancelar.isPending} variant="destructive">
              {cancelar.isPending ? "Cancelando..." : "Cancelar Item"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
