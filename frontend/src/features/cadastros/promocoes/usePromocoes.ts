import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { toast } from "@/lib/toast";

export interface PromoçaoResponse {
  id: number;
  tenant_id: number;
  nome: string;
  descricao: string | null;
  tipo_desconto: "porcentagem" | "valor_fixo";
  valor_desconto: number;
  data_inicio: string;
  data_fim: string | null;
  hora_inicio: string | null;
  hora_fim: string | null;
  recorrencia: "nenhuma" | "semanal" | "mensal";
  dias_semana: number[] | null;
  dias_mes: number[] | null;
  produto_ids: number[];
  criado_por: number | null;
  created_at: string | null;
}

export interface PromoçaoCreate {
  nome: string;
  descricao?: string | null;
  tipo_desconto: "porcentagem" | "valor_fixo";
  valor_desconto: number;
  data_inicio: string;
  data_fim?: string | null;
  hora_inicio?: string | null;
  hora_fim?: string | null;
  recorrencia: "nenhuma" | "semanal" | "mensal";
  dias_semana?: number[] | null;
  dias_mes?: number[] | null;
  produto_ids?: number[];
}

export type PromoçaoUpdate = Partial<PromoçaoCreate>;

const QK = "promocoes";

export function usePromocoes(status?: string) {
  return useQuery<PromoçaoResponse[]>({
    queryKey: [QK, status],
    queryFn: () => {
      const params: Record<string, unknown> = {};
      if (status) params.status = status;
      return api.get<PromoçaoResponse[]>("/api/promocoes", { params }).then((r) => r.data);
    },
  });
}

export function usePromocoesMes(mes: string) {
  return useQuery<PromoçaoResponse[]>({
    queryKey: [QK, "mes", mes],
    queryFn: () =>
      api.get<PromoçaoResponse[]>("/api/promocoes/mes", { params: { mes } }).then((r) => r.data),
    enabled: !!mes,
  });
}

export function useCreatePromocao() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: PromoçaoCreate) =>
      api.post<PromoçaoResponse>("/api/promocoes", data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Promoção criada.");
    },
    onError: () => toast.error("Erro ao criar promoção."),
  });
}

export function useUpdatePromocao() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: PromoçaoUpdate }) =>
      api.patch<PromoçaoResponse>(`/api/promocoes/${id}`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Promoção atualizada.");
    },
    onError: () => toast.error("Erro ao atualizar promoção."),
  });
}

export function useDeletePromocao() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/api/promocoes/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Promoção removida.");
    },
    onError: () => toast.error("Erro ao remover promoção."),
  });
}
