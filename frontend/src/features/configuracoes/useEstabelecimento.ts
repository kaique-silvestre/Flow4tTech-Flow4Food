import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface EstabelecimentoData {
  id: number;
  nome: string;
  cnpj: string | null;
  endereco: string | null;
  telefone: string | null;
}

export interface EstabelecimentoUpdate {
  nome?: string;
  cnpj?: string;
  endereco?: string;
  telefone?: string;
}

export function useEstabelecimento() {
  return useQuery<EstabelecimentoData>({
    queryKey: ["config", "estabelecimento"],
    queryFn: () =>
      api.get<EstabelecimentoData>("/api/config/estabelecimento").then((r) => r.data),
  });
}

export function useUpdateEstabelecimento() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: EstabelecimentoUpdate) =>
      api.patch<EstabelecimentoData>("/api/config/estabelecimento", body).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["config", "estabelecimento"] }),
  });
}
