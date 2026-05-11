import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "@/lib/toast";
import { api } from "@/lib/api";
import type { GarcomCreateFormValues, GarcomFormValues } from "./garcomSchemas";

export interface Garcom {
  id: number;
  nome: string;
  ativo: boolean;
}

const QK = "garcons";

export function useGarcons() {
  return useQuery<Garcom[]>({
    queryKey: [QK],
    queryFn: () => api.get<Garcom[]>("/api/garcons").then((r) => r.data),
  });
}

export function useCreateGarcom() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: GarcomCreateFormValues) =>
      api.post<Garcom>("/api/garcons", data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Garçom criado.");
    },
    onError: () => toast.error("Erro ao criar garçom."),
  });
}

export function useToggleGarcomAtivo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      api.patch<Garcom>(`/api/garcons/${id}/toggle-ativo`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: [QK] }),
    onError: () => toast.error("Erro ao alternar status do garçom."),
  });
}

export function useUpdateGarcom() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: GarcomFormValues }) =>
      api.put<Garcom>(`/api/garcons/${id}`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Garçom atualizado.");
    },
    onError: () => toast.error("Erro ao atualizar garçom."),
  });
}
