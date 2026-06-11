import { useEffect, useState } from "react";
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
import { usePermissionTemplates, useAssignProfileTemplate } from "./usePermissionTemplates";

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
  const { data: templates = [] } = usePermissionTemplates();
  const assignTemplate = useAssignProfileTemplate();

  const [templateId, setTemplateId] = useState<number | null>(null);
  const templateActive = templateId !== null && !isAdmin;
  const locked = isAdmin || templateActive;

  const {
    register,
    handleSubmit,
    control,
    reset,
    setValue,
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
      setTemplateId(profile.template_id);
    } else {
      reset({ name: "", description: "", screens: [] });
      setTemplateId(null);
    }
  }, [profile, reset]);

  function applyTemplate(id: number | null) {
    setTemplateId(id);
    if (id !== null) {
      const tpl = templates.find((t) => t.id === id);
      if (tpl) setValue("screens", tpl.screens, { shouldValidate: true });
    }
    if (isEdit && profile) {
      assignTemplate.mutate({ profileId: profile.id, templateId: id });
    }
  }

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
          {!isAdmin && (
            <div className="space-y-1">
              <Label>Template de permissão</Label>
              <select
                className="w-full rounded-md border px-3 py-2 text-sm"
                value={templateId ?? ""}
                onChange={(e) =>
                  applyTemplate(e.target.value === "" ? null : Number(e.target.value))
                }
              >
                <option value="">Personalizado (sem template)</option>
                {templates.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.nome}
                    {t.is_system ? " (sistema)" : ""}
                  </option>
                ))}
              </select>
              {templateActive && (
                <Button
                  type="button"
                  variant="outline"
                  className="mt-1"
                  onClick={() => applyTemplate(null)}
                >
                  Personalizar
                </Button>
              )}
            </div>
          )}
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
                        disabled={locked}
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
