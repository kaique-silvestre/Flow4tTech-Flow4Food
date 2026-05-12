import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "@/lib/toast";
import { api } from "@/lib/api";
import type { GarcomCreateFormValues, GarcomFormValues } from "./garcomSchemas";

export interface Garcom {
  id: number;
  nome: string;
  ativo: boolean;
}

export interface ComissaoResponse {
  id: number;
  garcom_id: number;
  comanda_id: number;
  valor: number;
  percentual: number;
  pago: boolean;
  created_at: string;
}

export interface GarcomStatsResponse {
  garcom_id: number;
  total_comandas: number;
  comandas_fechadas: number;
  comissao_pendente: number;
  comissoes: ComissaoResponse[];
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

export function useGarcomStats(garcomId: number) {
  return useQuery<GarcomStatsResponse>({
    queryKey: [QK, garcomId, "stats"],
    queryFn: () =>
      api.get<GarcomStatsResponse>(`/api/garcons/${garcomId}/stats`).then((r) => r.data),
    enabled: garcomId > 0,
  });
}

export function useUpdateComissao() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, valor }: { id: number; valor: number }) =>
      api.patch<ComissaoResponse>(`/api/garcons/comissoes/${id}`, { valor }).then((r) => r.data),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: [QK, data.garcom_id, "stats"] });
      toast.success("Comissão atualizada.");
    },
    onError: () => toast.error("Erro ao atualizar comissão."),
  });
}

export function useTogglePagoComissao() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      api.patch<ComissaoResponse>(`/api/garcons/comissoes/${id}/toggle-pago`).then((r) => r.data),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: [QK, data.garcom_id, "stats"] });
    },
    onError: () => toast.error("Erro ao alterar status da comissão."),
  });
}

export function useDeleteComissao() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, garcom_id }: { id: number; garcom_id: number }) =>
      api.delete(`/api/garcons/comissoes/${id}`).then(() => garcom_id),
    onSuccess: (garcom_id) => {
      qc.invalidateQueries({ queryKey: [QK, garcom_id, "stats"] });
      toast.success("Comissão excluída.");
    },
    onError: () => toast.error("Erro ao excluir comissão."),
  });
}
