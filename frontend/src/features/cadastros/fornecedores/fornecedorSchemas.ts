import { z } from "zod";

export const fornecedorSchema = z.object({
  nome: z.string().min(1, "Nome é obrigatório"),
  telefone: z.string().nullable().optional(),
  email: z.string().nullable().optional(),
});

export type FornecedorFormValues = z.infer<typeof fornecedorSchema>;
