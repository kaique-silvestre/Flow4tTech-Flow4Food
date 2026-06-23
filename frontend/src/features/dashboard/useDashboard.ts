import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface HoraBucket {
  hora: number;
  faturamento: number;
}

export interface ProdutoTop {
  item_id: number;
  nome: string;
  quantidade: number;
  faturamento: number;
}

export interface DiaFaturamento {
  data: string;
  faturamento: number;
}

export interface ComandaAbertaItem {
  id: number;
  identificacao: string;
  qtd_itens: number;
  total: number;
  aberta_ha_minutos: number;
}

export interface EntregaEsperadaItem {
  compra_id: number;
  fornecedor_nome: string;
  data_prevista_recebimento: string;
  total: number;
}

export interface InsumoCriticoItem {
  nome: string;
  estoque_atual: number;
  nivel_critico: number;
  unidade_base: string;
}

export interface DashboardData {
  faturamento_hoje: number;
  ticket_medio_hoje: number;
  cmv_hoje: number;
  comandas_abertas: number;
  comandas_fechadas_hoje: number;
  lucro_estimado_hoje: number;
  faturamento_por_hora: HoraBucket[];
  top_10_produtos: ProdutoTop[];
  ultimos_30_dias: DiaFaturamento[];
  heatmap_mes: DiaFaturamento[];
  comandas_abertas_lista: ComandaAbertaItem[];
  contas_vencendo_7_dias_total: number;
  contas_vencendo_7_dias_qtd: number;
  entregas_esperadas_7_dias: EntregaEsperadaItem[];
  insumos_criticos: InsumoCriticoItem[];
  faturamento_ontem: number;
  faturamento_7d: number;
  faturamento_7d_anterior: number;
  faturamento_mes_atual: number;
  faturamento_mes_anterior: number;
}

export function useDashboard() {
  return useQuery<DashboardData>({
    queryKey: ["dashboard"],
    queryFn: () => api.get<DashboardData>("/api/dashboard").then((r) => r.data),
    refetchInterval: 60_000,
  });
}

export interface DashboardHistoricoItem {
  data: string;
  faturamento: number;
  total_compras: number;
}

export interface DashboardResumoAnualItem {
  mes: number;
  faturamento: number;
  total_compras: number;
}

export function useDashboardHistorico(inicio: string, fim: string) {
  return useQuery<DashboardHistoricoItem[]>({
    queryKey: ["dashboard", "historico", inicio, fim],
    queryFn: () =>
      api
        .get<DashboardHistoricoItem[]>("/api/dashboard/historico", { params: { inicio, fim } })
        .then((r) => r.data),
    enabled: !!inicio && !!fim,
  });
}

export function useDashboardResumoAnual(ano: number) {
  return useQuery<DashboardResumoAnualItem[]>({
    queryKey: ["dashboard", "resumo-anual", ano],
    queryFn: () =>
      api
        .get<DashboardResumoAnualItem[]>("/api/dashboard/resumo-anual", { params: { ano } })
        .then((r) => r.data),
  });
}
