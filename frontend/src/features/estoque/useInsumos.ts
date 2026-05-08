import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { toast } from "@/lib/toast";

export interface InsumoResponse {
  id: number;
  nome: string;
  categoria_id: number | null;
  unidade_base: string;
  quantidade_caixa: number | null;
  custo_medio: number | null;
  estoque_atual: number;
  ativo: boolean;
}

export interface InsumoCreateRequest {
  nome: string;
  unidade_base: string;
  categoria_id?: number | null;
  quantidade_caixa?: number | null;
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

export function useCreateInsumo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: InsumoCreateRequest) =>
      api.post<InsumoResponse>("/api/insumos", data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Insumo criado.");
    },
    onError: () => toast.error("Erro ao criar insumo."),
  });
}
