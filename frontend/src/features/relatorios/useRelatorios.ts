import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface PagamentoResumo {
  metodo_id: number;
  metodo_nome: string;
  total: number;
  qtd: number;
}

export interface ComandaRelatorioItem {
  id: number;
  identificacao: string;
  garcom_nome: string;
  total: number;
  desconto_percentual: number | null;
  desconto_valor: number | null;
  cortesias: number;
  data_fechamento: string;
  pagamentos: PagamentoResumo[];
}

export interface VendasDoDiaResponse {
  data: string;
  qtd_comandas: number;
  faturamento_bruto: number;
  total_descontos: number;
  total_cortesias: number;
  faturamento_liquido: number;
  por_metodo: PagamentoResumo[];
  comandas: ComandaRelatorioItem[];
}

export interface HistoricoResponse {
  total: number;
  comandas: ComandaRelatorioItem[];
}

export interface FechamentoCaixaResponse {
  data: string;
  qtd_comandas: number;
  faturamento_bruto: number;
  descontos: number;
  cortesias: number;
  faturamento_liquido: number;
  por_metodo: PagamentoResumo[];
}

export function useVendasDoDia() {
  return useQuery<VendasDoDiaResponse>({
    queryKey: ["relatorios", "vendas-do-dia"],
    queryFn: () =>
      api.get<VendasDoDiaResponse>("/api/relatorios/vendas-do-dia").then((r) => r.data),
  });
}

export function useHistoricoComandas(params: {
  data_inicio: string;
  data_fim: string;
  garcom_id?: number | null;
  busca?: string;
}) {
  return useQuery<HistoricoResponse>({
    queryKey: ["relatorios", "historico", params],
    queryFn: () =>
      api
        .get<HistoricoResponse>("/api/relatorios/historico-comandas", {
          params: {
            data_inicio: params.data_inicio,
            data_fim: params.data_fim,
            garcom_id: params.garcom_id ?? undefined,
            busca: params.busca || undefined,
          },
        })
        .then((r) => r.data),
    enabled: !!params.data_inicio && !!params.data_fim,
  });
}

export function useFechamentoCaixa(data: string) {
  return useQuery<FechamentoCaixaResponse>({
    queryKey: ["relatorios", "fechamento-caixa", data],
    queryFn: () =>
      api
        .get<FechamentoCaixaResponse>("/api/relatorios/fechamento-caixa", { params: { data } })
        .then((r) => r.data),
    enabled: !!data,
  });
}
