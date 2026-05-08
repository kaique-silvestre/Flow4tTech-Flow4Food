import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "@/lib/toast";
import { api } from "@/lib/api";
import type { ItemFormValues } from "./itemSchemas";

export interface ComponenteResponse {
  insumo_id: number;
  insumo_nome: string;
  quantidade: number;
  unidade_base: string;
}

export interface ItemResponse {
  id: number;
  nome: string;
  categoria_id: number | null;
  tipo: "simples" | "composto";
  vendavel: boolean;
  unidade_base: "un" | "g";
  quantidade_caixa: number | null;
  custo_medio: number | null;
  preco_venda: number | null;
  estoque_atual: number;
  ativo: boolean;
  custo_composto: number | null;
  cmv_percentual: number | null;
  componentes: ComponenteResponse[] | null;
}

export interface ItemFilters {
  categoria_id?: number | null;
  tipo?: string | null;
  vendavel?: boolean | null;
  busca?: string | null;
}

const QK = "itens";

function filtersToParams(filters: ItemFilters) {
  const p: Record<string, string> = {};
  if (filters.categoria_id != null) p.categoria_id = String(filters.categoria_id);
  if (filters.tipo != null) p.tipo = filters.tipo;
  if (filters.vendavel != null) p.vendavel = String(filters.vendavel);
  if (filters.busca) p.busca = filters.busca;
  return p;
}

export function useItens(filters: ItemFilters = {}) {
  return useQuery<ItemResponse[]>({
    queryKey: [QK, filters],
    queryFn: () =>
      api.get<ItemResponse[]>("/api/itens", { params: filtersToParams(filters) }).then((r) => r.data),
  });
}

export function useItensSimples() {
  return useQuery<ItemResponse[]>({
    queryKey: [QK, "simples"],
    queryFn: () => api.get<ItemResponse[]>("/api/itens/simples").then((r) => r.data),
  });
}

export function useCreateItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ItemFormValues) =>
      api.post<ItemResponse>("/api/itens", data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Item criado.");
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message;
      toast.error(msg ?? "Erro ao criar item.");
    },
  });
}

export function useUpdateItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ItemFormValues }) =>
      api.put<ItemResponse>(`/api/itens/${id}`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Item atualizado.");
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message;
      toast.error(msg ?? "Erro ao atualizar item.");
    },
  });
}

export function useDeleteItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/api/itens/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Item removido.");
    },
    onError: () => toast.error("Erro ao remover item."),
  });
}
