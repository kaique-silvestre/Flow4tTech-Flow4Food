import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "@/lib/toast";
import { api, type ApiErrorBody } from "@/lib/api";
import type { ProdutoResponse } from "@/features/cadastros/produtos/useProdutos";
import type { CancelarItemValues, LancarItemValues, NovaComandaValues } from "./comandaSchemas";

export interface ItemComandaResponse {
  id: number;
  item_id: number;
  item_nome: string;
  quantidade: number;
  preco_unitario: number;
  subtotal: number;
  pessoa_associada: string | null;
  observacao: string | null;
  cortesia: boolean;
  cancelado: boolean;
  motivo_cancelamento: string | null;
  estornado: boolean;
  created_at: string;
}

export interface PagamentoResponse {
  id: number;
  metodo_id: number;
  metodo_nome: string;
  valor: number;
}

export interface ComandaResponse {
  id: number;
  identificacao: string;
  tipo_identificacao: "nome" | "mesa";
  garcom_id: number;
  garcom_nome: string;
  status: "aberta" | "fechada" | "cancelada" | "reaberta";
  version: number;
  pessoas: string[];
  total_parcial: number;
  itens_ativos: ItemComandaResponse[];
  created_at: string;
  tempo_aberta_minutos: number;
  desconto_percentual: number | null;
  desconto_valor: number | null;
  total: number | null;
  saldo_pendente: number | null;
  data_fechamento: string | null;
  pagamentos: PagamentoResponse[];
  itens_negativos: string[];
}

function handle409(err: unknown, comanda_id: number | string, qc: ReturnType<typeof useQueryClient>) {
  const axiosErr = err as { response?: { status?: number; data?: ApiErrorBody } };
  if (axiosErr?.response?.status === 409) {
    toast.error("Comanda alterada por outro usuário, recarregue");
    qc.invalidateQueries({ queryKey: ["comandas", comanda_id] });
  } else {
    const msg = axiosErr?.response?.data?.error?.message;
    toast.error(msg ?? "Erro ao processar operação");
  }
}

export function useComandas(busca?: string) {
  return useQuery<ComandaResponse[]>({
    queryKey: ["comandas", busca],
    queryFn: () =>
      api
        .get<ComandaResponse[]>("/api/comandas", { params: busca ? { busca } : {} })
        .then((r) => r.data),
  });
}

export function useComanda(id: number | string) {
  return useQuery<ComandaResponse>({
    queryKey: ["comandas", id],
    queryFn: () => api.get<ComandaResponse>(`/api/comandas/${id}`).then((r) => r.data),
  });
}

export function useAbrirComanda() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  return useMutation({
    mutationFn: (data: NovaComandaValues) =>
      api.post<ComandaResponse>("/api/comandas", data).then((r) => r.data),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["comandas"] });
      navigate(`/comandas/${data.id}`);
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: ApiErrorBody } })?.response?.data?.error?.message;
      toast.error(msg ?? "Erro ao abrir comanda");
    },
  });
}

export function useLancarItem(comanda_id: number | string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ version, ...data }: LancarItemValues & { version: number }) =>
      api
        .post<ComandaResponse>(`/api/comandas/${comanda_id}/itens`, { ...data, version })
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["comandas", comanda_id] });
    },
    onError: (err: unknown) => handle409(err, comanda_id, qc),
  });
}

export function useEditarItem(comanda_id: number | string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      item_id,
      version,
      quantidade,
      pessoa_associada,
      observacao,
    }: {
      item_id: number;
      version: number;
      quantidade?: number;
      pessoa_associada?: string;
      observacao?: string;
    }) =>
      api
        .patch<ComandaResponse>(`/api/comandas/${comanda_id}/itens/${item_id}`, {
          version,
          quantidade,
          pessoa_associada,
          observacao,
        })
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["comandas", comanda_id] });
    },
    onError: (err: unknown) => handle409(err, comanda_id, qc),
  });
}

export function useCancelarItem(comanda_id: number | string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      item_id,
      version,
      ...data
    }: CancelarItemValues & { item_id: number; version: number }) =>
      api
        .post<ComandaResponse>(`/api/comandas/${comanda_id}/itens/${item_id}/cancelar`, {
          ...data,
          version,
        })
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["comandas", comanda_id] });
    },
    onError: (err: unknown) => handle409(err, comanda_id, qc),
  });
}

export function useComandasFechadas(busca?: string) {
  return useQuery<ComandaResponse[]>({
    queryKey: ["comandas", "fechadas", busca],
    queryFn: () =>
      api
        .get<ComandaResponse[]>("/api/comandas/fechadas", { params: busca ? { busca } : {} })
        .then((r) => r.data),
  });
}

export function useReopenComanda(comanda_id: number | string) {
  const qc = useQueryClient();
  const navigate = useNavigate();
  return useMutation({
    mutationFn: () =>
      api.post<ComandaResponse>(`/api/comandas/${comanda_id}/reabrir`).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["comandas"] });
      navigate(`/comandas/${comanda_id}`);
      toast.success("Comanda reaberta com sucesso");
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: ApiErrorBody } })?.response?.data?.error?.message;
      toast.error(msg ?? "Erro ao reabrir comanda");
    },
  });
}

export function useTopItens(dias = 7, limit = 6) {
  return useQuery<ProdutoResponse[]>({
    queryKey: ["produtos", "top", { dias, limit }],
    queryFn: () =>
      api
        .get<ProdutoResponse[]>("/api/produtos/top", { params: { dias, limit } })
        .then((r) => r.data),
  });
}
