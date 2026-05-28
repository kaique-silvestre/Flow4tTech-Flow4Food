import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "@/lib/toast";
import { api, type ApiErrorBody } from "@/lib/api";

export interface CaixaMovimento {
  id: number;
  sessao_id: number;
  tipo: string;
  valor: number;
  motivo: string;
  user_id: number;
  created_at: string;
}

export interface CaixaSessao {
  id: number;
  status: string;
  valor_abertura: number;
  valor_informado?: number;
  valor_esperado?: number;
  diferenca?: number;
  aberto_por_user_id: number;
  fechado_por_user_id?: number;
  opened_at: string;
  closed_at?: string;
  observacao?: string;
  created_at: string;
  movimentos: CaixaMovimento[];
}

export function useSessaoAberta() {
  return useQuery<CaixaSessao | null>({
    queryKey: ["caixa", "sessao"],
    queryFn: async () => {
      try {
        const r = await api.get<CaixaSessao>("/api/caixa/sessao");
        return r.data;
      } catch (err: unknown) {
        const status = (err as { response?: { status?: number } })?.response?.status;
        if (status === 404) return null;
        throw err;
      }
    },
    retry: false,
  });
}

export function useAbrirCaixa() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (valor_abertura: number) =>
      api.post<CaixaSessao>("/api/caixa/abrir", { valor_abertura }).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["caixa"] });
      toast.success("Caixa aberto");
    },
    onError: (err: unknown) => {
      const axiosErr = err as { response?: { data?: ApiErrorBody } };
      const code = axiosErr?.response?.data?.error?.code;
      if (code === "SESSAO_JA_ABERTA") {
        toast.error("Já existe uma sessão de caixa aberta");
      } else {
        toast.error(axiosErr?.response?.data?.error?.message ?? "Erro ao abrir caixa");
      }
    },
  });
}

export function useFecharCaixa() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { valor_informado: number; observacao?: string }) =>
      api.post<CaixaSessao>("/api/caixa/fechar", data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["caixa"] });
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: ApiErrorBody } })?.response?.data?.error?.message;
      toast.error(msg ?? "Erro ao fechar caixa");
    },
  });
}

export function useRegistrarMovimento() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { tipo: "sangria" | "suprimento"; valor: number; motivo: string }) =>
      api.post<CaixaMovimento>("/api/caixa/movimentos", data).then((r) => r.data),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["caixa"] });
      const label = vars.tipo === "sangria" ? "Sangria" : "Suprimento";
      toast.success(`${label} registrado`);
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: ApiErrorBody } })?.response?.data?.error?.message;
      toast.error(msg ?? "Erro ao registrar movimento");
    },
  });
}
