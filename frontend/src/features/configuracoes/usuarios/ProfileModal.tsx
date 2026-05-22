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
import { useCreateProfile, useUpdateProfile, type ProfileResponse } from "./useProfiles";

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

const schema = z.object({
  name: z.string().min(1, "Obrigatório"),
  description: z.string().optional(),
  screens: z.array(z.string()).min(1, "Selecione ao menos uma tela"),
});

type FormValues = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  profile?: ProfileResponse;
}

export function ProfileModal({ open, onClose, profile }: Props) {
  const isEdit = !!profile;
  const isAdmin = profile?.name === "Admin";
  const createProfile = useCreateProfile();
  const updateProfile = useUpdateProfile(profile?.id ?? 0);

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", description: "", screens: [] },
  });

  useEffect(() => {
    if (profile) {
      reset({
        name: profile.name,
        description: profile.description ?? "",
        screens: profile.permissions,
      });
    } else {
      reset({ name: "", description: "", screens: [] });
    }
  }, [profile, reset]);

  async function onSubmit(data: FormValues) {
    if (isEdit) {
      await updateProfile.mutateAsync({ name: data.name, description: data.description, screens: data.screens });
    } else {
      await createProfile.mutateAsync({ name: data.name, description: data.description, screens: data.screens });
    }
    onClose();
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{isEdit ? (isAdmin ? "Ver Perfil" : "Editar Perfil") : "Novo Perfil"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1">
            <Label>Nome do perfil</Label>
            <Input {...register("name")} disabled={isAdmin} />
            {errors.name && <p className="text-xs text-red-500">{errors.name.message}</p>}
          </div>
          <div className="space-y-1">
            <Label>Descrição (opcional)</Label>
            <Input {...register("description")} disabled={isAdmin} />
          </div>
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
                        disabled={isAdmin}
                        checked={field.value.includes(screen.id)}
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
            {errors.screens && <p className="text-xs text-red-500">{errors.screens.message}</p>}
          </div>
          {profile && (
            <p className="text-xs text-gray-500">
              Usuários com este perfil: {profile.user_count}
            </p>
          )}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>CANCELAR</Button>
            {!isAdmin && (
              <Button type="submit" disabled={isSubmitting}>SALVAR PERFIL</Button>
            )}
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
