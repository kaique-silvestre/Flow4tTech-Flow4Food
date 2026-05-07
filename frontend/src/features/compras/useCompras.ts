import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { CompraFormValues } from "./compraSchemas";

export interface ItemCompraResponse {
  item_id: number;
  item_nome: string;
  quantidade: number;
  custo_unitario: number;
  custo_total: number;
}

export interface CompraResponse {
  id: number;
  fornecedor_id: number | null;
  fornecedor_nome: string | null;
  data_compra: string;
  numero_nota: string | null;
  total: number;
  itens: ItemCompraResponse[];
  created_at: string;
}

export interface CompraFilters {
  data_inicio?: string | null;
  data_fim?: string | null;
  fornecedor_id?: number | null;
}

const QK = "compras";

function filtersToParams(f: CompraFilters) {
  const p: Record<string, string> = {};
  if (f.data_inicio) p.data_inicio = f.data_inicio;
  if (f.data_fim) p.data_fim = f.data_fim;
  if (f.fornecedor_id != null) p.fornecedor_id = String(f.fornecedor_id);
  return p;
}

export function useCompras(filters: CompraFilters = {}) {
  return useQuery<CompraResponse[]>({
    queryKey: [QK, filters],
    queryFn: () =>
      api.get<CompraResponse[]>("/api/compras", { params: filtersToParams(filters) }).then((r) => r.data),
  });
}

export function useCreateCompra() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  return useMutation({
    mutationFn: (data: CompraFormValues) =>
      api.post<CompraResponse>("/api/compras", data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      qc.invalidateQueries({ queryKey: ["estoque"] });
      qc.invalidateQueries({ queryKey: ["itens"] });
      toast.success("Compra registrada.");
      navigate("/compras");
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message;
      toast.error(msg ?? "Erro ao registrar compra.", { duration: Infinity });
    },
  });
}
