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
