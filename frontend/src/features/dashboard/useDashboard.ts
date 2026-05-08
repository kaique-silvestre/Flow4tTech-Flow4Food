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
