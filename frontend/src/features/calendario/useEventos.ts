import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "@/lib/toast";
import { api } from "@/lib/api";

export interface EventoResponse {
  id: number;
  tenant_id: number;
  titulo: string;
  descricao: string | null;
  data_evento: string;
  criado_por: number | null;
  created_at: string | null;
}

export interface EventoCreate {
  titulo: string;
  descricao?: string | null;
  data_evento: string;
}

export interface EventoPatch {
  titulo?: string;
  descricao?: string | null;
}

const QK = "eventos";

export function useEventos(mes: string) {
  return useQuery<EventoResponse[]>({
    queryKey: [QK, mes],
    queryFn: async () => {
      const { data } = await api.get<EventoResponse[]>("/api/eventos", { params: { mes } });
      return data;
    },
  });
}

export function useCreateEvento() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: EventoCreate) => api.post<EventoResponse>("/api/eventos", data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Evento criado.");
    },
    onError: () => toast.error("Erro ao criar evento."),
  });
}

export function usePatchEvento() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: EventoPatch }) =>
      api.patch<EventoResponse>(`/api/eventos/${id}`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Evento atualizado.");
    },
    onError: () => toast.error("Erro ao atualizar evento."),
  });
}

export function useDeleteEvento() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/api/eventos/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Evento removido.");
    },
    onError: () => toast.error("Erro ao remover evento."),
  });
}
