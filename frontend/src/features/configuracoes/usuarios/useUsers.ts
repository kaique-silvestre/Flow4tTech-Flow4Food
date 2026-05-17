import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { toast } from "@/lib/toast";

export interface UserResponse {
  id: number;
  tenant_id: number;
  profile_id: number;
  profile_name: string;
  name: string;
  username: string;
  email: string | null;
  is_active: boolean;
  last_login: string | null;
  created_at: string;
}

export interface UserCreate {
  name: string;
  username: string;
  email?: string;
  profile_id: number;
  password: string;
  is_active: boolean;
}

export interface UserUpdate {
  name?: string;
  email?: string;
  profile_id?: number;
  is_active?: boolean;
}

function errMsg(e: unknown, fallback: string): string {
  if (e && typeof e === "object" && "response" in e) {
    const r = (e as { response?: { data?: { error?: { message?: string } } } }).response;
    return r?.data?.error?.message ?? fallback;
  }
  return fallback;
}

export function useUsers(search?: string, profileId?: number) {
  return useQuery({
    queryKey: ["users", search ?? "", profileId ?? null],
    queryFn: () => {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (profileId != null) params.set("profile_id", String(profileId));
      return api.get<UserResponse[]>(`/api/users?${params}`).then((r) => r.data);
    },
  });
}

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: UserCreate) => api.post<UserResponse>("/api/users", data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      toast.success("Usuário cadastrado");
    },
    onError: (e: unknown) => toast.error(errMsg(e, "Erro ao cadastrar")),
  });
}

export function useUpdateUser(userId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: UserUpdate) =>
      api.put<UserResponse>(`/api/users/${userId}`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      toast.success("Usuário atualizado");
    },
    onError: (e: unknown) => toast.error(errMsg(e, "Erro ao atualizar")),
  });
}

export function useDeleteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/api/users/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      toast.success("Usuário excluído");
    },
    onError: (e: unknown) => toast.error(errMsg(e, "Erro ao excluir")),
  });
}

export function useToggleUserActive() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.patch<UserResponse>(`/api/users/${id}/activate`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
    onError: (e: unknown) => toast.error(errMsg(e, "Erro")),
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: (id: number) =>
      api.post<{ temp_password: string }>(`/api/users/${id}/reset-password`).then((r) => r.data),
    onSuccess: (data) => toast.success(`Senha provisória: ${data.temp_password}`, { duration: 10000 }),
    onError: (e: unknown) => toast.error(errMsg(e, "Erro")),
  });
}

export function useCheckUsername(username: string, skip = false) {
  return useQuery({
    queryKey: ["check-username", username],
    queryFn: () =>
      api.get<{ available: boolean }>(`/api/users/check-username?username=${encodeURIComponent(username)}`).then((r) => r.data),
    enabled: !!username && !skip,
  });
}

export function useCheckEmail(email: string, skip = false) {
  return useQuery({
    queryKey: ["check-email", email],
    queryFn: () =>
      api.get<{ available: boolean }>(`/api/users/check-email?email=${encodeURIComponent(email)}`).then((r) => r.data),
    enabled: !!email && !skip,
  });
}
