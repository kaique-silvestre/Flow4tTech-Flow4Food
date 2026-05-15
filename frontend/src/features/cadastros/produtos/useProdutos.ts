import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { toast } from "@/lib/toast";

export interface FichaTecnicaItem {
  insumo_id: number;
  insumo_nome: string;
  quantidade: number;
  unidade_base: string;
  custo_medio_insumo: number | null;
}

export interface ProdutoResponse {
  id: number;
  nome: string;
  categoria_id: number | null;
  preco_venda: number | null;
  ativo: boolean;
  ficha_tecnica: FichaTecnicaItem[] | null;
  producao_possivel: number | null;
}

export interface ProdutoCreateRequest {
  nome: string;
  categoria_id?: number | null;
  preco_venda?: string | null;
  ficha_tecnica?: { insumo_id: number; quantidade: string }[];
}

export type ProdutoUpdateRequest = ProdutoCreateRequest;

const QK = "produtos";

export function useProdutos(busca?: string, options?: { ativo?: boolean }) {
  return useQuery<ProdutoResponse[]>({
    queryKey: [QK, busca, options?.ativo],
    queryFn: () => {
      const params: Record<string, unknown> = {};
      if (busca) params.busca = busca;
      if (options?.ativo !== undefined) params.ativo = options.ativo;
      return api.get<ProdutoResponse[]>("/api/produtos", { params }).then((r) => r.data);
    },
  });
}

export function useCreateProduto() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ProdutoCreateRequest) =>
      api.post<ProdutoResponse>("/api/produtos", data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Produto criado.");
    },
    onError: () => toast.error("Erro ao criar produto."),
  });
}

export function useUpdateProduto() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ProdutoUpdateRequest }) =>
      api.put<ProdutoResponse>(`/api/produtos/${id}`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Produto atualizado.");
    },
    onError: () => toast.error("Erro ao atualizar produto."),
  });
}

export function useDesativarProduto() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      api.patch<ProdutoResponse>(`/api/produtos/${id}/desativar`).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Produto desativado.");
    },
    onError: () => toast.error("Erro ao desativar produto."),
  });
}

export function useReativarProduto() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      api.patch<ProdutoResponse>(`/api/produtos/${id}/reativar`).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Produto reativado.");
    },
    onError: () => toast.error("Erro ao reativar produto."),
  });
}

export function useDeleteProduto() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/api/produtos/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Produto removido.");
    },
    onError: () => toast.error("Produto tem histórico em comandas. Use 'Desativar'."),
  });
}
