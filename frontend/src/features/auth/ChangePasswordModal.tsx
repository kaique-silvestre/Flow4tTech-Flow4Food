import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { toast } from "@/lib/toast";

const schema = z
  .object({
    current_password: z.string().min(1, "Obrigatório"),
    new_password: z.string().min(6, "Mínimo 6 caracteres"),
    confirm_password: z.string().min(1, "Obrigatório"),
  })
  .refine((d) => d.new_password === d.confirm_password, {
    message: "Senhas não coincidem",
    path: ["confirm_password"],
  });

type FormValues = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
}

export function ChangePasswordModal({ open, onClose }: Props) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const mutation = useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) =>
      api.post("/api/auth/change-password", data),
    onSuccess: () => {
      toast.success("Senha alterada com sucesso");
      reset();
      onClose();
    },
    onError: (e: unknown) => {
      const r = (e as { response?: { data?: { error?: { message?: string } } } }).response;
      toast.error(r?.data?.error?.message ?? "Erro ao alterar senha");
    },
  });

  function onSubmit(data: FormValues) {
    mutation.mutate({ current_password: data.current_password, new_password: data.new_password });
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Alterar Senha</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1">
            <Label>Senha atual</Label>
            <Input type="password" {...register("current_password")} />
            {errors.current_password && (
              <p className="text-xs text-red-500">{errors.current_password.message}</p>
            )}
          </div>
          <div className="space-y-1">
            <Label>Nova senha</Label>
            <Input type="password" {...register("new_password")} />
            {errors.new_password && (
              <p className="text-xs text-red-500">{errors.new_password.message}</p>
            )}
          </div>
          <div className="space-y-1">
            <Label>Confirmar nova senha</Label>
            <Input type="password" {...register("confirm_password")} />
            {errors.confirm_password && (
              <p className="text-xs text-red-500">{errors.confirm_password.message}</p>
            )}
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>CANCELAR</Button>
            <Button type="submit" disabled={isSubmitting || mutation.isPending}>ALTERAR</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
