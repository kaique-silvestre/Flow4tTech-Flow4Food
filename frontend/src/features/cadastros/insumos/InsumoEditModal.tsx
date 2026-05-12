import { useEffect } from "react";
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
import { useCreateInsumo, useUpdateInsumo, type InsumoResponse } from "@/features/estoque/useInsumos";

const schema = z.object({
  nome: z.string().min(1, "Nome obrigatório"),
  categoria_id: z.coerce.number().int().positive("Selecione uma categoria"),
  unidade_base: z.enum(["un", "g", "kg", "ml", "l"], { required_error: "Selecione uma unidade" }),
  quantidade_caixa: z.coerce.number().int().positive().optional().or(z.literal("")),
});

type FormValues = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  editing: InsumoResponse | null;
}

export function InsumoEditModal({ open, onClose, editing }: Props) {
  const { data: categoriasTree = [] } = useCategorias();
  const categorias = flattenCategorias(categoriasTree);
  const createMutation = useCreateInsumo();
  const updateMutation = useUpdateInsumo();

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  useEffect(() => {
    if (open) {
      if (editing) {
        reset({
          nome: editing.nome,
          categoria_id: editing.categoria_id ?? undefined,
          unidade_base: editing.unidade_base as FormValues["unidade_base"],
          quantidade_caixa: editing.quantidade_caixa ?? "",
        });
      } else {
        reset({ nome: "", categoria_id: undefined, unidade_base: undefined, quantidade_caixa: "" });
      }
    }
  }, [open, editing, reset]);

  const unidade = watch("unidade_base");

  function handleClose() {
    onClose();
  }

  function onSubmit(data: FormValues) {
    const payload = {
      nome: data.nome,
      categoria_id: data.categoria_id,
      unidade_base: data.unidade_base,
      quantidade_caixa: data.quantidade_caixa ? Number(data.quantidade_caixa) : null,
    };

    if (editing) {
      updateMutation.mutate(
        { id: editing.id, data: payload },
        { onSuccess: handleClose },
      );
    } else {
      createMutation.mutate(payload, { onSuccess: handleClose });
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{editing ? "Editar Insumo" : "Novo Insumo"}</DialogTitle>
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
              <option value="ml">ml (mililitros)</option>
              <option value="l">l (litros)</option>
            </select>
            {errors.unidade_base && <p className="text-xs text-red-500">{errors.unidade_base.message}</p>}
            {unidade === "kg" && <p className="text-xs text-gray-400">Compras poderão ser registradas em kg ou g</p>}
            {unidade === "g" && <p className="text-xs text-gray-400">Compras poderão ser registradas em g ou kg</p>}
            {unidade === "l" && <p className="text-xs text-gray-400">Compras poderão ser registradas em l ou ml</p>}
            {unidade === "ml" && <p className="text-xs text-gray-400">Compras poderão ser registradas em ml ou l</p>}
            {unidade === "un" && <p className="text-xs text-gray-400">Informe qtd por caixa abaixo para permitir compra em cx</p>}
          </div>

          {unidade === "un" && (
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
          )}

          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? "Salvando..." : editing ? "Salvar" : "Criar Insumo"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
