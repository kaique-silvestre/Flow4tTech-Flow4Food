import { z } from "zod";

export const garcomSchema = z.object({
  nome: z.string().min(1, "Nome é obrigatório"),
  ativo: z.boolean(),
});

export const garcomCreateSchema = z.object({
  nome: z.string().min(1, "Nome é obrigatório"),
});

export type GarcomFormValues = z.infer<typeof garcomSchema>;
export type GarcomCreateFormValues = z.infer<typeof garcomCreateSchema>;
