import { z } from "zod";

export const loginSchema = z.object({
  senha: z.string().min(1, "Senha obrigatória"),
});

export type LoginFormValues = z.infer<typeof loginSchema>;
