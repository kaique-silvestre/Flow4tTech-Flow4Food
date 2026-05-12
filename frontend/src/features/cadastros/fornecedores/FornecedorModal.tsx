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
import { fornecedorSchema, type FornecedorFormValues } from "./fornecedorSchemas";
import type { Fornecedor } from "./useFornecedores";
import { useCreateFornecedor, useUpdateFornecedor } from "./useFornecedores";

interface Props {
  open: boolean;
  onClose: () => void;
  editing?: Fornecedor | null;
  onCreated?: (forn: Fornecedor) => void;
}

export function FornecedorModal({ open, onClose, editing, onCreated }: Props) {
  const create = useCreateFornecedor();
  const update = useUpdateFornecedor();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FornecedorFormValues>({ resolver: zodResolver(fornecedorSchema) });

  useEffect(() => {
    reset(
      editing
        ? { nome: editing.nome, telefone: editing.telefone, email: editing.email }
        : { nome: "", telefone: "", email: "" }
    );
  }, [editing, open, reset]);

  const isPending = create.isPending || update.isPending;

  function onSubmit(data: FornecedorFormValues) {
    const payload = {
      ...data,
      telefone: data.telefone || null,
      email: data.email || null,
    };
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
          <DialogTitle>{editing ? "Editar Fornecedor" : "Novo Fornecedor"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="nome">Nome</Label>
            <Input id="nome" {...register("nome")} />
            {errors.nome && <p className="text-sm text-red-500">{errors.nome.message}</p>}
          </div>
          <div className="space-y-1">
            <Label htmlFor="telefone">Telefone</Label>
            <Input id="telefone" {...register("telefone")} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="email">E-mail</Label>
            <Input id="email" type="email" {...register("email")} />
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
