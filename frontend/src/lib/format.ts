import { format as fnsFormat } from "date-fns";
import { ptBR } from "date-fns/locale";

const currencyFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

export function formatCurrency(value: number | string): string {
  return currencyFormatter.format(Number(value));
}

/**
 * Parse an ISO datetime string returned by the API.
 * The backend stores UTC naive datetimes (no 'Z' suffix). Without 'Z',
 * JavaScript interprets the string as local time — wrong.
 * This function forces UTC parsing so the browser converts to local time correctly.
 */
export function parseApiDate(iso: string): Date {
  if (!iso) return new Date(NaN);
  const hasTimezone = iso.endsWith("Z") || /[+-]\d{2}:?\d{2}$/.test(iso);
  return new Date(hasTimezone ? iso : iso + "Z");
}

export function formatDate(d: Date | string, fmt = "dd/MM/yyyy HH:mm"): string {
  const date = typeof d === "string" ? parseApiDate(d) : d;
  return fnsFormat(date, fmt, { locale: ptBR });
}

export function formatQuantidade(value: number | string): string {
  const n = Number(value);
  if (Number.isInteger(n)) return String(n);
  return n.toLocaleString("pt-BR", { maximumFractionDigits: 3 });
}

// Display stock quantities: g and kg always shown as kg (3 decimals), others as integer.
export function stockDisplay(value: number | string, unidade_base: string): { qty: string; unit: string } {
  const n = Number(value);
  if (unidade_base === "g") {
    return {
      qty: (n / 1000).toLocaleString("pt-BR", { minimumFractionDigits: 3, maximumFractionDigits: 3 }),
      unit: "kg",
    };
  }
  if (unidade_base === "kg") {
    return {
      qty: n.toLocaleString("pt-BR", { minimumFractionDigits: 3, maximumFractionDigits: 3 }),
      unit: "kg",
    };
  }
  return {
    qty: Math.round(n).toLocaleString("pt-BR"),
    unit: unidade_base,
  };
}

// Custo médio always per kg for weight items (g stored as R$/g → convert to R$/kg).
export function formatCustoMedio(custo_medio: number | null | undefined, unidade_base: string): string {
  if (custo_medio == null) return "—";
  const isWeight = unidade_base === "g" || unidade_base === "kg";
  const displayUnit = isWeight ? "kg" : unidade_base;
  const displayValue = unidade_base === "g" ? Number(custo_medio) * 1000 : Number(custo_medio);
  return `${formatCurrency(displayValue)}/${displayUnit}`;
}
