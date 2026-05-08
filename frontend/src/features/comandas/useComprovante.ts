import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface EstabelecimentoInfo {
  nome: string;
  cnpj: string | null;
  endereco: string | null;
  telefone: string | null;
}

export interface ItemComprovanteRow {
  nome: string;
  quantidade: number;
  preco_unitario: number;
  subtotal: number;
  cortesia: boolean;
}

export interface PagamentoComprovanteRow {
  metodo_nome: string;
  valor: number;
}

export interface ComprovanteResponse {
  comanda_id: number;
  identificacao: string;
  tipo_identificacao: string;
  garcom_nome: string;
  data_fechamento: string | null;
  estabelecimento: EstabelecimentoInfo;
  itens: ItemComprovanteRow[];
  subtotal: number;
  desconto_percentual: number | null;
  desconto_valor: number | null;
  total: number | null;
  pagamentos: PagamentoComprovanteRow[];
}

export function useComprovante(id: number | string | undefined) {
  return useQuery<ComprovanteResponse>({
    queryKey: ["comprovante", id],
    queryFn: () =>
      api.get<ComprovanteResponse>(`/api/comandas/${id}/comprovante`).then((r) => r.data),
    enabled: !!id,
  });
}
