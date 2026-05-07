import { z } from "zod";

export const metodoPagamentoSchema = z.object({
  nome: z.string().min(1, "Nome é obrigatório"),
  ativo: z.boolean(),
});

export const metodoPagamentoCreateSchema = z.object({
  nome: z.string().min(1, "Nome é obrigatório"),
});

export type MetodoPagamentoFormValues = z.infer<typeof metodoPagamentoSchema>;
export type MetodoPagamentoCreateFormValues = z.infer<typeof metodoPagamentoCreateSchema>;
