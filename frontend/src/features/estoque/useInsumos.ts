import axios from "axios";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type ApiErrorBody } from "@/lib/api";
import { toast } from "@/lib/toast";

function conflictMsg(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err) && err.response?.status === 409) {
    return (err.response.data as ApiErrorBody)?.error?.message ?? "Já existe um insumo com este nome";
  }
  return fallback;
}

export interface InsumoResponse {
  id: number;
  nome: string;
  categoria_id: number | null;
  unidade_base: string;
  quantidade_caixa: number | null;
  custo_medio: number | null;
  estoque_atual: number;
  estoque_reservado: number;
  estoque_disponivel: number;
  nivel_critico: number | null;
  ativo: boolean;
}

export interface InsumoCreateRequest {
  nome: string;
  unidade_base: string;
  categoria_id?: number | null;
  quantidade_caixa?: number | null;
}

export interface InsumoUpdateRequest {
  nome: string;
  unidade_base: string;
  categoria_id: number | null;
  quantidade_caixa: number | null;
  nivel_critico: number | null;
}

const QK = "insumos";

export function useInsumos(busca?: string) {
  return useQuery<InsumoResponse[]>({
    queryKey: [QK, busca],
    queryFn: () =>
      api
        .get<InsumoResponse[]>("/api/insumos", { params: busca ? { busca } : {} })
        .then((r) => r.data),
  });
}

export function useAllInsumos(busca?: string) {
  return useQuery<InsumoResponse[]>({
    queryKey: [QK, "all", busca],
    queryFn: () =>
      api
        .get<InsumoResponse[]>("/api/insumos", {
          params: { incluir_inativos: true, ...(busca ? { busca } : {}) },
        })
        .then((r) => r.data),
  });
}

export function useCreateInsumo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: InsumoCreateRequest) =>
      api.post<InsumoResponse>("/api/insumos", data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Insumo criado.");
    },
    onError: (err) => toast.error(conflictMsg(err, "Erro ao criar insumo.")),
  });
}

export function useUpdateInsumo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: InsumoUpdateRequest }) =>
      api.put<InsumoResponse>(`/api/insumos/${id}`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Insumo atualizado.");
    },
    onError: (err) => toast.error(conflictMsg(err, "Erro ao atualizar insumo.")),
  });
}

export function useToggleInsumoAtivo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      api.patch<InsumoResponse>(`/api/insumos/${id}/toggle-ativo`).then((r) => r.data),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success(data.ativo ? "Insumo reativado." : "Insumo desativado.");
    },
    onError: () => toast.error("Erro ao alterar status do insumo."),
  });
}

export function useDeleteInsumo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/api/insumos/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Insumo removido.");
    },
    onError: () => toast.error("Erro ao remover insumo."),
  });
}
