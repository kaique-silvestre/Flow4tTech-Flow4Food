import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export type CockpitTipo = "evento" | "promocao" | "conta_pagar" | "entrega_insumo";

export interface CockpitItem {
  tipo: CockpitTipo;
  referencia_id: number;
  data_referencia: string; // YYYY-MM-DD
  descricao: string;
  hora_inicio: string | null;
  valor: number | null;
  fornecedor_nome: string | null;
}

const QK = "cockpit-consolidado";

export function useConsolidado(mes: string) {
  return useQuery<CockpitItem[]>({
    queryKey: [QK, mes],
    queryFn: async () => {
      const { data } = await api.get<CockpitItem[]>("/api/calendario/consolidado", {
        params: { mes },
      });
      return data;
    },
  });
}
