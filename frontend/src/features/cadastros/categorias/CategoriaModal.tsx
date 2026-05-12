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
import { useCategorias, useCreateCategoria, useUpdateCategoria } from "./useCategorias";

interface Props {
  open: boolean;
  onClose: () => void;
  editing?: Categoria | null;
  onCreated?: (cat: Categoria) => void;
}

export function CategoriaModal({ open, onClose, editing, onCreated }: Props) {
  const create = useCreateCategoria();
  const update = useUpdateCategoria();
  const { data: categorias = [] } = useCategorias();

  const rootCategorias = categorias.filter(
    (c) => !c.parent_id && c.id !== editing?.id
  );

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CategoriaFormValues>({ resolver: zodResolver(categoriaSchema) });

  useEffect(() => {
    reset(
      editing
        ? { nome: editing.nome, parent_id: editing.parent_id ?? null }
        : { nome: "", parent_id: null }
    );
  }, [editing, open, reset]);

  const isPending = create.isPending || update.isPending;

  function onSubmit(data: CategoriaFormValues) {
    const payload = { ...data, parent_id: data.parent_id || null };
    if (editing) {
      update.mutate({ id: editing.id, data: payload }, { onSuccess: onClose });
    } else {
      create.mutate(payload, {
        onSuccess: (created) => {
          onCreated?.(created);
          onClose();
        },
      });
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

          <div className="space-y-1">
            <Label>Categoria pai (opcional)</Label>
            <select
              className="w-full rounded border px-2 py-1.5 text-sm"
              {...register("parent_id", {
                setValueAs: (v) => (v === "" || v === "0" ? null : Number(v)),
              })}
            >
              <option value="">— Sem categoria pai (raiz) —</option>
              {rootCategorias.map((c) => (
                <option key={c.id} value={c.id}>{c.nome}</option>
              ))}
            </select>
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
