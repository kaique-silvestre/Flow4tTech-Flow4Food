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
import { useCategorias, flattenCategorias } from "@/features/cadastros/categorias/useCategorias";
import { useCreateInsumo, type InsumoResponse } from "@/features/estoque/useInsumos";

const insumoRapidoSchema = z.object({
  nome: z.string().min(1, "Nome obrigatório"),
  categoria_id: z.coerce.number().int().positive("Selecione uma categoria"),
  unidade_base: z.enum(["un", "g", "kg"], { required_error: "Selecione uma unidade" }),
});

type InsumoRapidoFormValues = z.infer<typeof insumoRapidoSchema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess: (insumo: InsumoResponse) => void;
}

export function InsumoModal({ open, onClose, onSuccess }: Props) {
  const { data: categoriasTree = [] } = useCategorias();
  const categorias = flattenCategorias(categoriasTree);
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
        quantidade_caixa: null,
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
                <option key={c.id} value={c.id}>
                  {c.indent ? `  ${c.nome}` : c.nome}
                </option>
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
            </select>
            {errors.unidade_base && <p className="text-xs text-red-500">{errors.unidade_base.message}</p>}
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
