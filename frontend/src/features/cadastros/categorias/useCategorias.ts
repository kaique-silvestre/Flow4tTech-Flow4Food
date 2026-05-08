import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "@/lib/toast";
import { api } from "@/lib/api";
import type { CategoriaFormValues } from "./categoriaSchemas";

export interface Categoria {
  id: number;
  nome: string;
}

const QK = "categorias";

export function useCategorias() {
  return useQuery<Categoria[]>({
    queryKey: [QK],
    queryFn: () => api.get<Categoria[]>("/api/categorias").then((r) => r.data),
  });
}

export function useCreateCategoria() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CategoriaFormValues) =>
      api.post<Categoria>("/api/categorias", data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Categoria criada.");
    },
    onError: () => toast.error("Erro ao criar categoria."),
  });
}

export function useUpdateCategoria() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: CategoriaFormValues }) =>
      api.put<Categoria>(`/api/categorias/${id}`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Categoria atualizada.");
    },
    onError: () => toast.error("Erro ao atualizar categoria."),
  });
}

export function useDeleteCategoria() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/api/categorias/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Categoria removida.");
    },
    onError: () => toast.error("Erro ao remover categoria."),
  });
}
