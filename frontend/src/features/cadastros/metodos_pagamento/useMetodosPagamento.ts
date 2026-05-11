import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "@/lib/toast";
import { api, type ApiErrorBody } from "@/lib/api";
import type { MetodoPagamentoCreateFormValues, MetodoPagamentoFormValues } from "./metodoPagamentoSchemas";

export interface MetodoPagamento {
  id: number;
  nome: string;
  ativo: boolean;
}

const QK = "metodos-pagamento";

export function useMetodosPagamento() {
  return useQuery<MetodoPagamento[]>({
    queryKey: [QK],
    queryFn: () => api.get<MetodoPagamento[]>("/api/metodos-pagamento").then((r) => r.data),
  });
}

export function useCreateMetodoPagamento() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: MetodoPagamentoCreateFormValues) =>
      api.post<MetodoPagamento>("/api/metodos-pagamento", data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Método de pagamento criado.");
    },
    onError: () => toast.error("Erro ao criar método de pagamento."),
  });
}

export function useUpdateMetodoPagamento() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: MetodoPagamentoFormValues }) =>
      api.put<MetodoPagamento>(`/api/metodos-pagamento/${id}`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Método de pagamento atualizado.");
    },
    onError: () => toast.error("Erro ao atualizar método de pagamento."),
  });
}

export function useToggleMetodoAtivo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      api.patch<MetodoPagamento>(`/api/metodos-pagamento/${id}/toggle-ativo`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: [QK] }),
    onError: () => toast.error("Erro ao alternar status do método."),
  });
}

export function useDeleteMetodoPagamento() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/api/metodos-pagamento/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Método removido.");
    },
    onError: (err: unknown) => {
      const code = (err as { response?: { data?: ApiErrorBody } })?.response?.data?.error?.code;
      if (code === "CONFLICT") {
        toast.error("Método de pagamento possui histórico e não pode ser removido.");
      } else {
        toast.error("Erro ao remover método de pagamento.");
      }
    },
  });
}
