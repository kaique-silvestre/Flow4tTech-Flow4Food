import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type ApiErrorBody } from "@/lib/api";
import { toast } from "@/lib/toast";

export interface ItemConsumoInternoResponse {
  id: number;
  consumidor_id: number;
  consumidor_nome: string;
  produto_id: number;
  produto_nome: string;
  quantidade: number;
  custo_unitario: number;
  subtotal: number;
  observacao: string | null;
  created_at: string;
}

export interface ResumoConsumidorResponse {
  consumidor_id: number;
  consumidor_nome: string;
  itens_no_mes: number;
  total: number;
  ultima_atividade: string | null;
}

interface LancarConsumoRequest {
  consumidor_id: number;
  produto_id: number;
  quantidade: number;
  observacao?: string;
}

interface LancarConsumoBatchItem {
  produto_id: number;
  quantidade: number;
  observacao?: string;
}

export interface LancarConsumoBatchRequest {
  consumidor_id: number;
  itens: LancarConsumoBatchItem[];
}

interface LancarConsumoBatchResponse {
  itens: ItemConsumoInternoResponse[];
}

function errMsg(e: unknown, fallback: string): string {
  const r = (e as { response?: { data?: ApiErrorBody } })?.response?.data;
  return r?.error?.message ?? fallback;
}

export interface PeriodParams {
  mes?: number;
  ano?: number;
  data_inicio?: string;
  data_fim?: string;
}

export function useResumoConsumo(period?: PeriodParams) {
  return useQuery<ResumoConsumidorResponse[]>({
    queryKey: ["consumo_interno", "resumo", period],
    queryFn: () => {
      const params: Record<string, string | number> = {};
      if (period?.data_inicio) {
        params.data_inicio = period.data_inicio;
        params.data_fim = period.data_fim!;
      } else {
        if (period?.mes != null) params.mes = period.mes;
        if (period?.ano != null) params.ano = period.ano;
      }
      return api
        .get<ResumoConsumidorResponse[]>("/api/consumo-interno/resumo", { params })
        .then((r) => r.data);
    },
  });
}

export function useItensConsumo(filters?: {
  consumidor_id?: number;
  mes?: number;
  ano?: number;
  data_inicio?: string;
  data_fim?: string;
}) {
  return useQuery<ItemConsumoInternoResponse[]>({
    queryKey: ["consumo_interno", "itens", filters],
    queryFn: () => {
      const params: Record<string, string | number> = {};
      if (filters?.consumidor_id != null) params.consumidor_id = filters.consumidor_id;
      if (filters?.data_inicio) {
        params.data_inicio = filters.data_inicio;
        params.data_fim = filters.data_fim!;
      } else {
        if (filters?.mes != null) params.mes = filters.mes;
        if (filters?.ano != null) params.ano = filters.ano;
      }
      return api
        .get<ItemConsumoInternoResponse[]>("/api/consumo-interno", { params })
        .then((r) => r.data);
    },
  });
}

export function useLancarConsumo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: LancarConsumoRequest) =>
      api.post<ItemConsumoInternoResponse>("/api/consumo-interno", data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["consumo_interno"] });
      qc.invalidateQueries({ queryKey: ["insumos"] });
      qc.invalidateQueries({ queryKey: ["estoque"] });
      toast.success("Consumo registrado com sucesso");
    },
    onError: (e: unknown) => toast.error(errMsg(e, "Erro ao registrar consumo")),
  });
}

export function useLancarConsumoBatch() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: LancarConsumoBatchRequest) =>
      api.post<LancarConsumoBatchResponse>("/api/consumo-interno/batch", data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["consumo_interno"] });
      qc.invalidateQueries({ queryKey: ["insumos"] });
      qc.invalidateQueries({ queryKey: ["estoque"] });
      toast.success("Consumo registrado com sucesso");
    },
    onError: (e: unknown) => toast.error(errMsg(e, "Erro ao registrar consumo")),
  });
}

export function useEstornarConsumo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (itemId: number) =>
      api.delete(`/api/consumo-interno/${itemId}`).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["consumo_interno"] });
      qc.invalidateQueries({ queryKey: ["insumos"] });
      qc.invalidateQueries({ queryKey: ["estoque"] });
      toast.success("Consumo estornado com sucesso");
    },
    onError: (e: unknown) => toast.error(errMsg(e, "Erro ao estornar consumo")),
  });
}
