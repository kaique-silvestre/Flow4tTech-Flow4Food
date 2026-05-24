import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "@/lib/toast";
import { api } from "@/lib/api";

export interface ContaPagarResponse {
  id: number;
  compra_id: number | null;
  fornecedor_id: number | null;
  fornecedor_nome: string | null;
  valor: number;
  data_vencimento: string;
  data_pagamento: string | null;
  status: string;
  metodo_pagamento_id: number | null;
  observacao: string | null;
  created_at: string;
}

export interface ContasPagarPageResponse {
  itens: ContaPagarResponse[];
  total: number;
  pagina: number;
  por_pagina: number;
  total_paginas: number;
  total_pendente: number;
  total_vencido: number;
}

export interface ContasPagarResumoResponse {
  pendente: number;
  vencido: number;
  total_vencido: number;
}

export interface PagarContaRequest {
  metodo_pagamento_id?: number | null;
  data_pagamento: string;
  observacao?: string | null;
}

export interface ContaFilters {
  status?: string | null;
  data_vencimento_inicio?: string | null;
  data_vencimento_fim?: string | null;
  fornecedor_id?: number | null;
  pagina?: number;
  por_pagina?: number;
}

const QK = "contas-pagar";

function filtersToParams(f: ContaFilters) {
  const p: Record<string, string> = {};
  if (f.status) p.status = f.status;
  if (f.data_vencimento_inicio) p.data_vencimento_inicio = f.data_vencimento_inicio;
  if (f.data_vencimento_fim) p.data_vencimento_fim = f.data_vencimento_fim;
  if (f.fornecedor_id != null) p.fornecedor_id = String(f.fornecedor_id);
  if (f.pagina != null) p.pagina = String(f.pagina);
  if (f.por_pagina != null) p.por_pagina = String(f.por_pagina);
  return p;
}

export function useContasPagar(filters: ContaFilters = {}) {
  return useQuery<ContasPagarPageResponse>({
    queryKey: [QK, filters],
    queryFn: () =>
      api.get<ContasPagarPageResponse>("/api/contas-pagar", { params: filtersToParams(filters) }).then((r) => r.data),
  });
}

export function useContasPagarResumo() {
  return useQuery<ContasPagarResumoResponse>({
    queryKey: [QK, "resumo"],
    queryFn: () =>
      api.get<ContasPagarResumoResponse>("/api/contas-pagar/resumo").then((r) => r.data),
    staleTime: 30_000,
  });
}

export function usePagarConta() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: PagarContaRequest }) =>
      api.post<ContaPagarResponse>(`/api/contas-pagar/${id}/pagar`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Pagamento registrado.");
    },
    onError: () => toast.error("Erro ao registrar pagamento."),
  });
}

export interface NotificacaoResponse {
  id: number;
  tipo: string;
  referencia_id: number | null;
  mensagem: string;
  lida: boolean;
  created_at: string;
}

export function useNotificacoes() {
  return useQuery<NotificacaoResponse[]>({
    queryKey: ["notificacoes"],
    queryFn: () =>
      api.get<NotificacaoResponse[]>("/api/contas-pagar/notificacoes").then((r) => r.data),
    staleTime: 60_000,
  });
}

export function useMarcarNotificacaoLida() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      api.post(`/api/contas-pagar/notificacoes/${id}/marcar-lida`).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notificacoes"] });
    },
  });
}
