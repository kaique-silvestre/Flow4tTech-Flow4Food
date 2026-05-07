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
import { garcomCreateSchema, garcomSchema, type GarcomCreateFormValues, type GarcomFormValues } from "./garcomSchemas";
import type { Garcom } from "./useGarcons";
import { useCreateGarcom, useUpdateGarcom } from "./useGarcons";

interface Props {
  open: boolean;
  onClose: () => void;
  editing?: Garcom | null;
}

export function GarcomModal({ open, onClose, editing }: Props) {
  const create = useCreateGarcom();
  const update = useUpdateGarcom();

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<GarcomFormValues>({
    resolver: zodResolver(editing ? garcomSchema : garcomCreateSchema as typeof garcomSchema),
    defaultValues: { ativo: true },
  });

  const ativo = watch("ativo");

  useEffect(() => {
    reset(editing ? { nome: editing.nome, ativo: editing.ativo } : { nome: "", ativo: true });
  }, [editing, open, reset]);

  const isPending = create.isPending || update.isPending;

  function onSubmit(data: GarcomFormValues) {
    if (editing) {
      update.mutate({ id: editing.id, data }, { onSuccess: onClose });
    } else {
      const createData: GarcomCreateFormValues = { nome: data.nome };
      create.mutate(createData, { onSuccess: onClose });
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>{editing ? "Editar Garçom" : "Novo Garçom"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="nome">Nome</Label>
            <Input id="nome" {...register("nome")} />
            {errors.nome && <p className="text-sm text-red-500">{errors.nome.message}</p>}
          </div>
          {editing && (
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setValue("ativo", !ativo)}
                className={`relative h-6 w-11 rounded-full transition-colors ${ativo ? "bg-gray-900" : "bg-gray-300"}`}
              >
                <span
                  className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${ativo ? "translate-x-5" : "translate-x-0.5"}`}
                />
              </button>
              <Label>{ativo ? "Ativo" : "Inativo"}</Label>
            </div>
          )}
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
