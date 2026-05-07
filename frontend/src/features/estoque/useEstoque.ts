import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { BaixaSemVendaFormValues } from "./estoqueSchemas";

export interface SaldoItemResponse {
  id: number;
  nome: string;
  categoria_id: number | null;
  categoria_nome: string | null;
  unidade_base: string;
  estoque_atual: number;
  custo_medio: number | null;
}

export interface MovimentoResponse {
  id: number;
  item_id: number;
  item_nome: string;
  tipo: "entrada" | "saida_venda" | "saida_perda";
  quantidade: number;
  custo_unitario: number | null;
  saldo_apos: number;
  motivo: string | null;
  observacao: string | null;
  compra_id: number | null;
  created_at: string;
}

export interface MovimentoListResponse {
  itens: MovimentoResponse[];
  total: number;
  pagina: number;
  por_pagina: number;
}

export interface SaldoFilters {
  categoria_id?: number | null;
  busca?: string | null;
}

export interface MovimentoFilters {
  item_id?: number | null;
  tipo?: string | null;
  data_inicio?: string | null;
  data_fim?: string | null;
  pagina?: number;
  por_pagina?: number;
}

const QK = "estoque";

export function useSaldoEstoque(filters: SaldoFilters = {}) {
  const params: Record<string, string> = {};
  if (filters.categoria_id != null) params.categoria_id = String(filters.categoria_id);
  if (filters.busca) params.busca = filters.busca;

  return useQuery<SaldoItemResponse[]>({
    queryKey: [QK, "saldo", filters],
    queryFn: () => api.get<SaldoItemResponse[]>("/api/estoque/saldo", { params }).then((r) => r.data),
  });
}

export function useMovimentos(filters: MovimentoFilters = {}) {
  const params: Record<string, string> = {};
  if (filters.item_id != null) params.item_id = String(filters.item_id);
  if (filters.tipo) params.tipo = filters.tipo;
  if (filters.data_inicio) params.data_inicio = filters.data_inicio;
  if (filters.data_fim) params.data_fim = filters.data_fim;
  if (filters.pagina) params.pagina = String(filters.pagina);
  if (filters.por_pagina) params.por_pagina = String(filters.por_pagina);

  return useQuery<MovimentoListResponse>({
    queryKey: [QK, "movimentos", filters],
    queryFn: () => api.get<MovimentoListResponse>("/api/estoque/movimentos", { params }).then((r) => r.data),
  });
}

export function useBaixaSemVenda() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: BaixaSemVendaFormValues) =>
      api.post<{ movimento: MovimentoResponse; saldo_negativo: boolean }>("/api/estoque/baixa-sem-venda", data).then((r) => r.data),
    onSuccess: (result) => {
      qc.invalidateQueries({ queryKey: [QK] });
      qc.invalidateQueries({ queryKey: ["itens"] });
      if (result.saldo_negativo) {
        toast.warning("Baixa registrada. Estoque ficou negativo.");
      } else {
        toast.success("Baixa registrada.");
      }
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message;
      toast.error(msg ?? "Erro ao registrar baixa.", { duration: Infinity });
    },
  });
}
