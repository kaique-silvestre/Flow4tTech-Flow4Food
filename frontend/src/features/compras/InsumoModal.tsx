import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
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
import { useCreateInsumo, type InsumoResponse } from "@/features/estoque/useInsumos";

const insumoRapidoSchema = z.object({
  nome: z.string().min(1, "Nome obrigatório"),
  categoria_id: z.coerce.number().int().positive("Selecione uma categoria"),
  unidade_base: z.enum(["un", "g", "kg", "ml", "l"], { required_error: "Selecione uma unidade" }),
  quantidade_caixa: z.coerce.number().int().positive().optional().or(z.literal("")),
});

type InsumoRapidoFormValues = z.infer<typeof insumoRapidoSchema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess: (insumo: InsumoResponse) => void;
}

export function InsumoModal({ open, onClose, onSuccess }: Props) {
  const { data: categorias = [] } = useCategorias();
  const createInsumo = useCreateInsumo();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<InsumoRapidoFormValues>({
    resolver: zodResolver(insumoRapidoSchema),
  });

  function handleClose() {
    reset();
    onClose();
  }

  function onSubmit(data: InsumoRapidoFormValues) {
    createInsumo.mutate(
      {
        nome: data.nome,
        categoria_id: data.categoria_id,
        unidade_base: data.unidade_base,
        quantidade_caixa: data.quantidade_caixa ? Number(data.quantidade_caixa) : null,
      },
      {
        onSuccess: (insumo) => {
          reset();
          onSuccess(insumo);
        },
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Cadastrar Insumo</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="insumo-nome">Nome *</Label>
            <Input id="insumo-nome" {...register("nome")} />
            {errors.nome && <p className="text-xs text-red-500">{errors.nome.message}</p>}
          </div>

          <div className="space-y-1">
            <Label>Categoria *</Label>
            <select
              className="w-full rounded border px-2 py-1.5 text-sm"
              {...register("categoria_id")}
            >
              <option value="">Selecione...</option>
              {categorias.map((c) => (
                <option key={c.id} value={c.id}>{c.nome}</option>
              ))}
            </select>
            {errors.categoria_id && <p className="text-xs text-red-500">{errors.categoria_id.message}</p>}
          </div>

          <div className="space-y-1">
            <Label>Unidade *</Label>
            <select
              className="w-full rounded border px-2 py-1.5 text-sm"
              {...register("unidade_base")}
            >
              <option value="">Selecione...</option>
              <option value="un">un (unidade)</option>
              <option value="g">g (gramas)</option>
              <option value="kg">kg (quilos)</option>
              <option value="ml">ml (mililitros)</option>
              <option value="l">l (litros)</option>
            </select>
            {errors.unidade_base && <p className="text-xs text-red-500">{errors.unidade_base.message}</p>}
          </div>

          <div className="space-y-1">
            <Label htmlFor="qtd-caixa">Qtd por caixa (opcional)</Label>
            <Input
              id="qtd-caixa"
              type="number"
              min="1"
              step="1"
              placeholder="Ex: 24"
              {...register("quantidade_caixa")}
            />
          </div>

          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createInsumo.isPending}>
              {createInsumo.isPending ? "Salvando..." : "Salvar Insumo"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
