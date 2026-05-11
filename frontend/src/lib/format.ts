import { format as fnsFormat } from "date-fns";
import { ptBR } from "date-fns/locale";

const currencyFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

export function formatCurrency(value: number | string): string {
  return currencyFormatter.format(Number(value));
}

export function formatDate(d: Date | string, fmt = "dd/MM/yyyy HH:mm"): string {
  const date = typeof d === "string" ? new Date(d) : d;
  return fnsFormat(date, fmt, { locale: ptBR });
}

export function formatQuantidade(value: number | string): string {
  const n = Number(value);
  if (Number.isInteger(n)) return String(n);
  return n.toLocaleString("pt-BR", { maximumFractionDigits: 3 });
}
