import { z } from "zod";

export const TIPOS_PAGAMENTO = ["dinheiro", "credito", "debito", "pix", "outro"] as const;
export type TipoPagamento = (typeof TIPOS_PAGAMENTO)[number];

export const TIPO_LABELS: Record<TipoPagamento, string> = {
  dinheiro: "Dinheiro",
  credito: "Crédito",
  debito: "Débito",
  pix: "Pix",
  outro: "Outro",
};

export const metodoPagamentoSchema = z.object({
  nome: z.string().min(1, "Nome é obrigatório"),
  ativo: z.boolean(),
  tipo: z.enum(TIPOS_PAGAMENTO),
});

export const metodoPagamentoCreateSchema = z.object({
  nome: z.string().min(1, "Nome é obrigatório"),
  tipo: z.enum(TIPOS_PAGAMENTO),
});

export type MetodoPagamentoFormValues = z.infer<typeof metodoPagamentoSchema>;
export type MetodoPagamentoCreateFormValues = z.infer<typeof metodoPagamentoCreateSchema>;
