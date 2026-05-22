import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateUser, useUpdateUser, useResetPassword, type UserResponse } from "./useUsers";
import { useProfiles } from "./useProfiles";

const ALPHABET = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789";
function generatePassword(len = 10): string {
  return Array.from({ length: len }, () =>
    ALPHABET[Math.floor(Math.random() * ALPHABET.length)]
  ).join("");
}

const createSchema = z.object({
  name: z.string().min(1, "Obrigatório"),
  username: z.string().min(1, "Obrigatório"),
  email: z.string().email("Email inválido").or(z.literal("")).optional(),
  profile_id: z.coerce.number().min(1, "Selecione um perfil"),
  password: z.string().min(6, "Mínimo 6 caracteres"),
  is_active: z.boolean(),
});

const editSchema = createSchema.omit({ password: true });

type CreateForm = z.infer<typeof createSchema>;

interface Props {
  open: boolean;
  onClose: () => void;
  user?: UserResponse;
}

export function UserModal({ open, onClose, user }: Props) {
  const isEdit = !!user;
  const { data: profiles = [] } = useProfiles();
  const createUser = useCreateUser();
  const updateUser = useUpdateUser(user?.id ?? 0);
  const resetPwd = useResetPassword();

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<CreateForm>({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    resolver: zodResolver((isEdit ? editSchema : createSchema) as any),
    defaultValues: {
      name: "",
      username: "",
      email: "",
      profile_id: 0,
      password: "",
      is_active: true,
    },
  });

  useEffect(() => {
    if (user) {
      reset({
        name: user.name,
        username: user.username,
        email: user.email ?? "",
        profile_id: user.profile_id,
        is_active: user.is_active,
      });
    } else {
      reset({ name: "", username: "", email: "", profile_id: 0, password: "", is_active: true });
    }
  }, [user, reset]);

  async function onSubmit(data: CreateForm) {
    const payload = {
      ...data,
      email: data.email || undefined,
    };
    if (isEdit) {
      await updateUser.mutateAsync({
        name: payload.name,
        email: payload.email,
        profile_id: payload.profile_id,
        is_active: payload.is_active,
      });
    } else {
      await createUser.mutateAsync(payload);
    }
    onClose();
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Editar Usuário" : "Cadastrar Usuário"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1">
            <Label>Nome completo</Label>
            <Input {...register("name")} />
            {errors.name && <p className="text-xs text-red-500">{errors.name.message}</p>}
          </div>
          <div className="space-y-1">
            <Label>Usuário (login)</Label>
            <Input {...register("username")} disabled={isEdit} />
            {errors.username && <p className="text-xs text-red-500">{errors.username.message}</p>}
          </div>
          <div className="space-y-1">
            <Label>Email</Label>
            <Input type="email" {...register("email")} />
            {errors.email && <p className="text-xs text-red-500">{errors.email.message}</p>}
          </div>
          <div className="space-y-1">
            <Label>Perfil</Label>
            <select
              {...register("profile_id", { valueAsNumber: true })}
              className="w-full rounded border px-3 py-2 text-sm"
            >
              <option value={0}>Selecione...</option>
              {profiles.filter((p) => p.is_active).map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
            {errors.profile_id && <p className="text-xs text-red-500">{errors.profile_id.message}</p>}
          </div>
          {!isEdit && (
            <div className="space-y-1">
              <Label>Senha provisória</Label>
              <div className="flex gap-2">
                <Input
                  type="text"
                  className="font-mono"
                  {...register("password")}
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const pwd = generatePassword();
                    setValue("password", pwd, { shouldValidate: true });
                  }}
                >
                  Gerar
                </Button>
              </div>
              {errors.password && <p className="text-xs text-red-500">{errors.password.message}</p>}
            </div>
          )}
          <div className="flex items-center gap-2">
            <input type="checkbox" id="is_active" {...register("is_active")} />
            <Label htmlFor="is_active">Ativo</Label>
          </div>
          <div className="flex justify-between gap-2">
            {isEdit && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => resetPwd.mutate(user!.id)}
              >
                Redefinir senha
              </Button>
            )}
            <div className="ml-auto flex gap-2">
              <Button type="button" variant="outline" onClick={onClose}>CANCELAR</Button>
              <Button type="submit" disabled={isSubmitting}>SALVAR USUÁRIO</Button>
            </div>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
