import { useEffect } from "react";
import { useForm, Controller } from "react-hook-form";
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
import {
  useCreateUser,
  useUpdateUser,
  useResetPassword,
  useUserPermissions,
  useSetUserPermissions,
  type UserResponse,
} from "./useUsers";
import { useProfiles } from "./useProfiles";
import { useAuthStore } from "@/stores/authStore";

const SCREENS: { id: string; label: string }[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "comandas", label: "Comandas / Cardápio" },
  { id: "compras", label: "Compras" },
  { id: "estoque", label: "Estoque" },
  { id: "cadastros", label: "Cadastros" },
  { id: "relatorios", label: "Relatórios" },
  { id: "configuracoes", label: "Configurações" },
  { id: "gestao_usuarios", label: "Gestão de Usuários" },
];

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
  profile_id: z.coerce.number().optional().nullable(),
  password: z.string().min(6, "Mínimo 6 caracteres"),
  is_active: z.boolean(),
  screens: z.array(z.string()),
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
  const isFreeUser = isEdit && user.profile_id == null;
  const currentUser = useAuthStore((s) => s.user);
  const isSelf = isEdit && currentUser?.user_id === user.id;
  const { data: profiles = [] } = useProfiles();
  const createUser = useCreateUser();
  const updateUser = useUpdateUser(user?.id ?? 0);
  const resetPwd = useResetPassword();
  const { data: existingPerms = [] } = useUserPermissions(user?.id ?? 0, isFreeUser);
  const setPerms = useSetUserPermissions(user?.id ?? 0);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    control,
    formState: { errors, isSubmitting },
  } = useForm<CreateForm>({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    resolver: zodResolver((isEdit ? editSchema : createSchema) as any),
    defaultValues: {
      name: "",
      username: "",
      email: "",
      profile_id: undefined,
      password: "",
      is_active: true,
      screens: [],
    },
  });

  const watchedProfileId = watch("profile_id");
  const showScreens = !watchedProfileId || watchedProfileId === 0;

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const existingPermsKey = existingPerms.join(",");

  useEffect(() => {
    if (user) {
      reset({
        name: user.name,
        username: user.username,
        email: user.email ?? "",
        profile_id: user.profile_id ?? undefined,
        is_active: user.is_active,
        screens: existingPerms,
      });
    } else {
      reset({ name: "", username: "", email: "", profile_id: undefined, password: "", is_active: true, screens: [] });
    }
  // existingPermsKey is a stable primitive derived from existingPerms to avoid new-array-reference re-runs
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id, existingPermsKey, reset]);

  async function onSubmit(data: CreateForm) {
    const profileId = data.profile_id && data.profile_id > 0 ? data.profile_id : null;
    const payload = {
      ...data,
      email: data.email || undefined,
      profile_id: profileId,
    };
    if (isEdit) {
      await updateUser.mutateAsync({
        name: payload.name,
        email: payload.email,
        profile_id: profileId ?? undefined,
        is_active: payload.is_active,
      });
      if (profileId == null) {
        await setPerms.mutateAsync(data.screens);
      }
    } else {
      const created = await createUser.mutateAsync({
        name: payload.name,
        username: payload.username,
        email: payload.email,
        profile_id: profileId,
        password: payload.password,
        is_active: payload.is_active,
      });
      if (profileId == null && data.screens.length > 0 && created?.id) {
        await setPerms.mutateAsync(data.screens);
      }
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
            <Label htmlFor="profile_id">Perfil (opcional)</Label>
            <select
              id="profile_id"
              {...register("profile_id", { valueAsNumber: true })}
              className="w-full rounded border px-3 py-2 text-sm"
              disabled={isSelf}
            >
              <option value={0}>Sem perfil fixo</option>
              {profiles.filter((p) => p.is_active).map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
            {isSelf && (
              <p className="text-xs text-gray-500">Você não pode alterar seu próprio perfil</p>
            )}
          </div>
          {showScreens && (
            <div className="space-y-2">
              <Label>Telas com acesso</Label>
              <Controller
                control={control}
                name="screens"
                render={({ field }) => (
                  <div className="space-y-1">
                    {SCREENS.map((screen) => (
                      <label key={screen.id} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={field.value.includes(screen.id)}
                          disabled={isSelf}
                          onChange={(e) => {
                            if (e.target.checked) {
                              field.onChange([...field.value, screen.id]);
                            } else {
                              field.onChange(field.value.filter((s) => s !== screen.id));
                            }
                          }}
                        />
                        <span>{screen.label}</span>
                      </label>
                    ))}
                  </div>
                )}
              />
              {isSelf && (
                <p className="text-xs text-gray-500">Você não pode alterar suas próprias permissões</p>
              )}
            </div>
          )}
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
