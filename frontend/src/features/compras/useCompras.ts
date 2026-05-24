import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "@/lib/toast";
import { api, type ApiErrorBody } from "@/lib/api";
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
  status: string;
  tipo_compra: string;
  data_prevista_recebimento: string | null;
  data_real_recebimento: string | null;
  data_prevista_pagamento: string | null;
  itens: ItemCompraResponse[];
  created_at: string;
  warning?: string | null;
}

export interface CompraFilters {
  data_inicio?: string | null;
  data_fim?: string | null;
  fornecedor_id?: number | null;
  status?: string | null;
  tipo_compra?: string | null;
  pagina?: number;
  por_pagina?: number;
}

export interface ComprasPageResponse {
  itens: CompraResponse[];
  total: number;
  pagina: number;
  por_pagina: number;
  total_paginas: number;
  total_periodo: number;
}

const QK = "compras";

function filtersToParams(f: CompraFilters) {
  const p: Record<string, string> = {};
  if (f.data_inicio) p.data_inicio = f.data_inicio;
  if (f.data_fim) p.data_fim = f.data_fim;
  if (f.fornecedor_id != null) p.fornecedor_id = String(f.fornecedor_id);
  if (f.status != null) p.status = f.status;
  if (f.tipo_compra != null) p.tipo_compra = f.tipo_compra;
  if (f.pagina != null) p.pagina = String(f.pagina);
  if (f.por_pagina != null) p.por_pagina = String(f.por_pagina);
  return p;
}

export function useCompras(filters: CompraFilters = {}) {
  return useQuery<ComprasPageResponse>({
    queryKey: [QK, filters],
    queryFn: () =>
      api.get<ComprasPageResponse>("/api/compras", { params: filtersToParams(filters) }).then((r) => r.data),
  });
}

export function useCreateCompra() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  return useMutation({
    mutationFn: (data: CompraFormValues) =>
      api.post<CompraResponse>("/api/compras", data).then((r) => r.data),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: [QK] });
      qc.invalidateQueries({ queryKey: ["estoque"] });
      qc.invalidateQueries({ queryKey: ["itens"] });
      qc.invalidateQueries({ queryKey: ["insumos"] });
      qc.invalidateQueries({ queryKey: ["contas-pagar"] });
      toast.success("Compra registrada.");
      if (data.warning) toast.warning(data.warning);
      navigate("/compras");
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message;
      toast.error(msg ?? "Erro ao registrar compra.");
    },
  });
}

export function useConfirmarRecebimento() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      api.post<CompraResponse>(`/api/compras/${id}/confirmar-recebimento`).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      qc.invalidateQueries({ queryKey: ["estoque"] });
      qc.invalidateQueries({ queryKey: ["insumos"] });
      qc.invalidateQueries({ queryKey: ["notificacoes"] });
      toast.success("Recebimento confirmado. Estoque atualizado.");
    },
    onError: () => toast.error("Erro ao confirmar recebimento."),
  });
}

export function useCancelarCompra() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      api.post<CompraResponse>(`/api/compras/${id}/cancelar`).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      qc.invalidateQueries({ queryKey: ["estoque"] });
      qc.invalidateQueries({ queryKey: ["insumos"] });
      qc.invalidateQueries({ queryKey: ["contas-pagar"] });
      toast.warning("Nota cancelada. Verifique o custo médio dos insumos afetados.", { duration: 6000 });
    },
    onError: (err: unknown) => {
      const code = (err as { response?: { data?: ApiErrorBody } })?.response?.data?.error?.code;
      if (code === "CONFLICT") {
        toast.error("Esta nota já foi cancelada.");
      } else {
        toast.error("Erro ao cancelar nota.");
      }
    },
  });
}

export function usePatchCompra() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: {
      id: number;
      data: {
        fornecedor_id?: number | null;
        data_compra?: string;
        numero_nota?: string | null;
        data_prevista_recebimento?: string | null;
        data_prevista_pagamento?: string | null;
      };
    }) =>
      api.patch<CompraResponse>(`/api/compras/${id}`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QK] });
      toast.success("Compra atualizada.");
    },
    onError: () => toast.error("Erro ao editar compra."),
  });
}
