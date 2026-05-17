import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { toast } from "@/lib/toast";

export interface ProfileResponse {
  id: number;
  tenant_id: number;
  name: string;
  description: string | null;
  is_system: boolean;
  permissions: string[];
  user_count: number;
  created_at: string;
}

export interface ProfileCreate {
  name: string;
  description?: string;
  screens: string[];
}

export interface ProfileUpdate {
  name?: string;
  description?: string;
  screens?: string[];
}

function errMsg(e: unknown, fallback: string): string {
  if (e && typeof e === "object" && "response" in e) {
    const r = (e as { response?: { data?: { error?: { message?: string } } } }).response;
    return r?.data?.error?.message ?? fallback;
  }
  return fallback;
}

export function useProfiles() {
  return useQuery({
    queryKey: ["profiles"],
    queryFn: () => api.get<ProfileResponse[]>("/api/profiles").then((r) => r.data),
  });
}

export function useCreateProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ProfileCreate) =>
      api.post<ProfileResponse>("/api/profiles", data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["profiles"] });
      toast.success("Perfil criado");
    },
    onError: (e: unknown) => toast.error(errMsg(e, "Erro ao criar")),
  });
}

export function useUpdateProfile(profileId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ProfileUpdate) =>
      api.put<ProfileResponse>(`/api/profiles/${profileId}`, data).then((r) => r.data),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["profiles"] });
      toast.success(`Permissões atualizadas para ${data.user_count} usuários`);
    },
    onError: (e: unknown) => toast.error(errMsg(e, "Erro ao salvar")),
  });
}

export function useDeleteProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/api/profiles/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["profiles"] });
      toast.success("Perfil excluído");
    },
    onError: (e: unknown) => toast.error(errMsg(e, "Erro ao excluir")),
  });
}
