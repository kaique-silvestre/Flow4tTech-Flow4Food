import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "@/lib/toast";
import { api, type ApiErrorBody } from "@/lib/api";
import type { ComandaResponse } from "./useComandas";
import type { AplicarDescontoValues, FecharComandaValues } from "./fechamentoSchemas";

export interface MetodoPagamento {
  id: number;
  nome: string;
  ativo: boolean;
}

export function useMetodosPagamento() {
  return useQuery<MetodoPagamento[]>({
    queryKey: ["metodos_pagamento"],
    queryFn: () => api.get<MetodoPagamento[]>("/api/metodos-pagamento").then((r) => r.data),
  });
}

export function useAplicarDesconto(comanda_id: number | string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: AplicarDescontoValues) => {
      const body =
        data.tipo === "percentual"
          ? { desconto_percentual: data.valor }
          : { desconto_valor: data.valor };
      return api.post<ComandaResponse>(`/api/comandas/${comanda_id}/desconto`, body).then((r) => r.data);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["comandas", comanda_id] });
      toast.success("Desconto aplicado");
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: ApiErrorBody } })?.response?.data?.error?.message;
      toast.error(msg ?? "Erro ao aplicar desconto");
    },
  });
}

export function useFecharComanda(comanda_id: number | string) {
  const qc = useQueryClient();
  const navigate = useNavigate();
  return useMutation({
    mutationFn: (data: FecharComandaValues) =>
      api.post<ComandaResponse>(`/api/comandas/${comanda_id}/fechar`, data).then((r) => r.data),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["comandas"] });
      if (data.itens_negativos && data.itens_negativos.length > 0) {
        toast.warning(`Estoque negativo em: ${data.itens_negativos.join(", ")}`, { duration: 6000 });
      }
      if (data.status === "fechada") {
        toast.success("Comanda fechada com sucesso");
        navigate(`/comprovante/${comanda_id}`);
      } else {
        toast.success("Pagamento parcial registrado");
        navigate(`/comandas/${comanda_id}`);
      }
    },
    onError: (err: unknown) => {
      const axiosErr = err as { response?: { status?: number; data?: ApiErrorBody } };
      const code = axiosErr?.response?.data?.error?.code;
      const msg = axiosErr?.response?.data?.error?.message;
      if (code === "PAGAMENTO_NAO_BATE") {
        toast.error("Soma dos pagamentos não confere com o total");
      } else if (code === "PESSOAS_INSUFICIENTES") {
        toast.error("Cadastre ao menos 2 pessoas na comanda para dividir por pessoa");
      } else {
        toast.error(msg ?? "Erro ao fechar comanda");
      }
    },
  });
}
