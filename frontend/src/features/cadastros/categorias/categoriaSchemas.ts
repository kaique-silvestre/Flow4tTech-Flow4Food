import { z } from "zod";

export const categoriaSchema = z.object({
  nome: z.string().min(1, "Nome é obrigatório"),
  parent_id: z.number().int().positive().nullable().optional(),
});

export type CategoriaFormValues = z.infer<typeof categoriaSchema>;
