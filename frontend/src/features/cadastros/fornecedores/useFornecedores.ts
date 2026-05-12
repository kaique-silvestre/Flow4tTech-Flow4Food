import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "@/lib/toast";
import { api } from "@/lib/api";
import type { FornecedorFormValues } from "./fornecedorSchemas";

export interface Fornecedor {
  id: number;
  nome: string;
  telefone: string | null;
  email: string | null;
  ativo: boolean;
}

const QK = "fornecedores";

export function useFornecedores() {
  return useQuery<Fornecedor[]>({
    queryKey: [QK],
    queryFn: () => api.get<Fornecedor[]>("/api/fornecedores").then((r) => r.data),
  });
}

export function useCreateFornecedor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: FornecedorFormValues) =>
      api.post<Fornecedor>("/api/fornecedores", data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Fornecedor criado.");
    },
    onError: () => toast.error("Erro ao criar fornecedor."),
  });
}

export function useUpdateFornecedor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: FornecedorFormValues }) =>
      api.put<Fornecedor>(`/api/fornecedores/${id}`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Fornecedor atualizado.");
    },
    onError: () => toast.error("Erro ao atualizar fornecedor."),
  });
}

export function useToggleFornecedorAtivo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.patch<Fornecedor>(`/api/fornecedores/${id}/toggle-ativo`).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
    },
    onError: () => toast.error("Erro ao alterar status do fornecedor."),
  });
}

export function useDeleteFornecedor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/api/fornecedores/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Fornecedor removido.");
    },
    onError: () => toast.error("Erro ao remover fornecedor."),
  });
}
