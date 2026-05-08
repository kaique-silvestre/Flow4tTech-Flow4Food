import { format as fnsFormat } from "date-fns";
import { ptBR } from "date-fns/locale";

const currencyFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

export function formatCurrency(value: number): string {
  return currencyFormatter.format(value);
}

export function formatDate(d: Date | string, fmt = "dd/MM/yyyy HH:mm"): string {
  const date = typeof d === "string" ? new Date(d) : d;
  return fnsFormat(date, fmt, { locale: ptBR });
}

export function formatQuantidade(value: number): string {
  if (Number.isInteger(value)) return String(value);
  return parseFloat(value.toFixed(3)).toString();
}
