import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "@/lib/toast";
import { api } from "@/lib/api";
import type { BaixaSemVendaFormValues } from "./estoqueSchemas";

export interface SaldoItemResponse {
  id: number;
  nome: string;
  categoria_id: number | null;
  categoria_nome: string | null;
  unidade_base: string;
  estoque_atual: number;
  estoque_reservado: number;
  estoque_disponivel: number;
  custo_medio: number | null;
  nivel_critico: number | null;
}

export interface MovimentoResponse {
  id: number;
  item_id: number;
  item_nome: string;
  unidade_base: string;
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

export interface SaldoPageResponse {
  itens: SaldoItemResponse[];
  total: number;
  pagina: number;
  por_pagina: number;
  total_paginas: number;
}

export interface SaldoFilters {
  categoria_id?: number | null;
  busca?: string | null;
  pagina?: number;
  por_pagina?: number;
}

export interface MovimentoFilters {
  item_id?: number | null;
  tipo?: string | null;
  data_inicio?: string | null;
  data_fim?: string | null;
  pagina?: number;
  por_pagina?: number;
}

export interface MovimentoProdutoResponse {
  id: number;
  produto_id: number;
  produto_nome: string;
  comanda_id: number;
  comanda_label: string;
  quantidade: number;
  preco_unitario: number;
  subtotal: number;
  cortesia: boolean;
  cancelado: boolean;
  pessoa_associada: string | null;
  created_at: string;
}

export interface MovimentoProdutoListResponse {
  itens: MovimentoProdutoResponse[];
  total: number;
  pagina: number;
  por_pagina: number;
}

export interface MovimentoProdutoFilters {
  produto_id?: number | null;
  data_inicio?: string | null;
  data_fim?: string | null;
  pagina?: number;
  por_pagina?: number;
}

const QK = "estoque";

export interface InsumoCriticoResponse {
  id: number;
  nome: string;
  unidade_base: string;
  estoque_disponivel: number;
  nivel_critico: number;
}

export function useInsumoCriticos() {
  return useQuery<InsumoCriticoResponse[]>({
    queryKey: [QK, "criticos"],
    queryFn: () => api.get<InsumoCriticoResponse[]>("/api/estoque/criticos").then((r) => r.data),
    staleTime: 60_000,
  });
}

export function useSaldoEstoque(filters: SaldoFilters = {}) {
  const params: Record<string, string> = {};
  if (filters.categoria_id != null) params.categoria_id = String(filters.categoria_id);
  if (filters.busca) params.busca = filters.busca;
  if (filters.pagina) params.pagina = String(filters.pagina);
  if (filters.por_pagina) params.por_pagina = String(filters.por_pagina);

  return useQuery<SaldoPageResponse>({
    queryKey: [QK, "saldo", filters],
    queryFn: () => api.get<SaldoPageResponse>("/api/estoque/saldo", { params }).then((r) => r.data),
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

export function useMovimentosProdutos(filters: MovimentoProdutoFilters = {}) {
  const params: Record<string, string> = {};
  if (filters.produto_id != null) params.produto_id = String(filters.produto_id);
  if (filters.data_inicio) params.data_inicio = filters.data_inicio;
  if (filters.data_fim) params.data_fim = filters.data_fim;
  if (filters.pagina) params.pagina = String(filters.pagina);
  if (filters.por_pagina) params.por_pagina = String(filters.por_pagina);

  return useQuery<MovimentoProdutoListResponse>({
    queryKey: [QK, "movimentos-produtos", filters],
    queryFn: () =>
      api.get<MovimentoProdutoListResponse>("/api/estoque/movimentos-produtos", { params }).then((r) => r.data),
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
      qc.invalidateQueries({ queryKey: ["insumos"] });
      if (result.saldo_negativo) {
        toast.warning("Baixa registrada. Estoque ficou negativo.");
      } else {
        toast.success("Baixa registrada.");
      }
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message;
      toast.error(msg ?? "Erro ao registrar baixa.");
    },
  });
}
