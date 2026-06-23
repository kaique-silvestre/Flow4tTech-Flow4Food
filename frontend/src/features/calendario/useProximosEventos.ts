import { useMemo } from "react";
import { useConsolidado, type CockpitItem } from "./useConsolidado";

function todayMes(): string {
  const n = new Date();
  return `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, "0")}`;
}
function todayStr(): string {
  const n = new Date();
  return `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, "0")}-${String(n.getDate()).padStart(2, "0")}`;
}

export type ProximoItem = CockpitItem & { diasRestantes: number };

export function useProximosEventos(maxItems = 3): { items: ProximoItem[]; isLoading: boolean } {
  const mes = todayMes();
  const { data = [], isLoading, isError } = useConsolidado(mes);

  const items = useMemo<ProximoItem[]>(() => {
    if (isError) return [];
    const today = todayStr();
    return data
      .filter((item) => item.data_referencia >= today)
      .sort((a, b) => a.data_referencia.localeCompare(b.data_referencia))
      .slice(0, maxItems)
      .map((item) => {
        const diff = Math.ceil(
          (new Date(item.data_referencia + "T12:00:00").getTime() - new Date(today + "T12:00:00").getTime()) /
            (1000 * 60 * 60 * 24),
        );
        return { ...item, diasRestantes: diff };
      });
  }, [data, isError, maxItems]);

  return { items, isLoading };
}
