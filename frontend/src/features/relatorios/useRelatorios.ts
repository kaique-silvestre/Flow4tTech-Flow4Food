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
  total_comissoes: number;
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
  total_comissoes: number;
  faturamento_liquido: number;
  por_metodo: PagamentoResumo[];
}

export function useVendasDoDia(data?: string) {
  return useQuery<VendasDoDiaResponse>({
    queryKey: ["relatorios", "vendas-do-dia", data],
    queryFn: () =>
      api
        .get<VendasDoDiaResponse>("/api/relatorios/vendas-do-dia", {
          params: data ? { data } : {},
        })
        .then((r) => r.data),
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

export interface ItemSemCusto {
  item_id: number;
  nome: string;
}

export interface DREResponse {
  mes: string;
  faturamento_bruto: number;
  descontos: number;
  cortesias_valor: number;
  faturamento_liquido: number;
  cmv: number;
  perdas: number;
  comissoes: number;
  total_custos: number;
  lucro_bruto: number;
  margem_percentual: number;
  produtos_sem_custo: ItemSemCusto[];
}

export interface CMVProdutoItem {
  item_id: number;
  nome: string;
  preco_venda: number | null;
  custo_medio: number | null;
  margem_valor: number | null;
  margem_percentual: number | null;
  classificacao: "verde" | "amarelo" | "vermelho" | "sem_custo";
}

export interface CMVPorProdutoResponse {
  itens: CMVProdutoItem[];
}

export interface PerdasGrupo {
  motivo: string;
  qtd_movimentos: number;
  total_valor: number;
}

export interface PerdasCortesiasResponse {
  data_inicio: string;
  data_fim: string;
  total_geral: number;
  grupos: PerdasGrupo[];
}

export interface VendasGarcomItem {
  garcom_id: number;
  garcom_nome: string;
  qtd_comandas: number;
  faturamento: number;
  ticket_medio: number;
  comissao: number;
}

export interface VendasPorGarcomResponse {
  data_inicio: string;
  data_fim: string;
  garcons: VendasGarcomItem[];
}

export function useDRE(mes: string) {
  return useQuery<DREResponse>({
    queryKey: ["relatorios", "dre", mes],
    queryFn: () =>
      api.get<DREResponse>("/api/relatorios/dre", { params: { mes } }).then((r) => r.data),
    enabled: !!mes,
  });
}

export function useCMVPorProduto() {
  return useQuery<CMVPorProdutoResponse>({
    queryKey: ["relatorios", "cmv-por-produto"],
    queryFn: () =>
      api.get<CMVPorProdutoResponse>("/api/relatorios/cmv-por-produto").then((r) => r.data),
  });
}

export function usePerdasCortesias(params: { data_inicio: string; data_fim: string }) {
  return useQuery<PerdasCortesiasResponse>({
    queryKey: ["relatorios", "perdas-cortesias", params],
    queryFn: () =>
      api
        .get<PerdasCortesiasResponse>("/api/relatorios/perdas-cortesias", { params })
        .then((r) => r.data),
    enabled: !!params.data_inicio && !!params.data_fim,
  });
}

export function useVendasPorGarcom(params: { data_inicio: string; data_fim: string }) {
  return useQuery<VendasPorGarcomResponse>({
    queryKey: ["relatorios", "vendas-por-garcom", params],
    queryFn: () =>
      api
        .get<VendasPorGarcomResponse>("/api/relatorios/vendas-por-garcom", { params })
        .then((r) => r.data),
    enabled: !!params.data_inicio && !!params.data_fim,
  });
}

export interface ProdutoMaisVendidoItem {
  produto_id: number;
  produto_nome: string;
  categoria_nome: string | null;
  quantidade_total: number;
  receita_total: number;
  percentual_receita: number;
}

export interface ProdutosMaisVendidosResponse {
  data_inicio: string;
  data_fim: string;
  receita_total_periodo: number;
  itens: ProdutoMaisVendidoItem[];
}

export function useProdutosMaisVendidos(params: { data_inicio: string; data_fim: string }) {
  return useQuery<ProdutosMaisVendidosResponse>({
    queryKey: ["relatorios", "produtos-mais-vendidos", params],
    queryFn: () =>
      api
        .get<ProdutosMaisVendidosResponse>("/api/relatorios/produtos-mais-vendidos", { params })
        .then((r) => r.data),
    enabled: !!params.data_inicio && !!params.data_fim,
  });
}

export interface HorarioPicoItem {
  hora: number;
  total_comandas: number;
  receita_total: number;
}

export interface PicoVendasHorarioResponse {
  data_inicio: string;
  data_fim: string;
  horarios: HorarioPicoItem[];
  hora_pico: number | null;
  total_comandas_periodo: number;
  receita_total_periodo: number;
}

export function usePicoVendasHorario(params: { data_inicio: string; data_fim: string }) {
  return useQuery<PicoVendasHorarioResponse>({
    queryKey: ["relatorios", "pico-vendas-horario", params],
    queryFn: () =>
      api
        .get<PicoVendasHorarioResponse>("/api/relatorios/pico-vendas-horario", { params })
        .then((r) => r.data),
    enabled: !!params.data_inicio && !!params.data_fim,
  });
}
