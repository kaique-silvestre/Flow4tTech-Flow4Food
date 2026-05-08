import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface ProdutoResponse {
  id: number;
  nome: string;
  categoria_id: number | null;
  preco_venda: number | null;
  ativo: boolean;
}

const QK = "produtos";

export function useProdutos(busca?: string) {
  return useQuery<ProdutoResponse[]>({
    queryKey: [QK, busca],
    queryFn: () =>
      api
        .get<ProdutoResponse[]>("/api/produtos", { params: busca ? { busca } : {} })
        .then((r) => r.data),
  });
}
