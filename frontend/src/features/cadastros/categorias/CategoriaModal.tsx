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
import { categoriaSchema, type CategoriaFormValues } from "./categoriaSchemas";
import type { Categoria } from "./useCategorias";
import { useCreateCategoria, useUpdateCategoria } from "./useCategorias";

interface Props {
  open: boolean;
  onClose: () => void;
  editing?: Categoria | null;
}

export function CategoriaModal({ open, onClose, editing }: Props) {
  const create = useCreateCategoria();
  const update = useUpdateCategoria();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CategoriaFormValues>({ resolver: zodResolver(categoriaSchema) });

  useEffect(() => {
    reset(editing ? { nome: editing.nome } : { nome: "" });
  }, [editing, open, reset]);

  const isPending = create.isPending || update.isPending;

  function onSubmit(data: CategoriaFormValues) {
    if (editing) {
      update.mutate({ id: editing.id, data }, { onSuccess: onClose });
    } else {
      create.mutate(data, { onSuccess: onClose });
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>{editing ? "Editar Categoria" : "Nova Categoria"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="nome">Nome</Label>
            <Input id="nome" {...register("nome")} />
            {errors.nome && <p className="text-sm text-red-500">{errors.nome.message}</p>}
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? "Salvando..." : "Salvar"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
