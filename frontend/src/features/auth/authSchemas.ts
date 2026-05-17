import { z } from "zod";

export const loginSchema = z.object({
  identifier: z.string().min(1, "Campo obrigatório"),
  password: z.string().min(1, "Campo obrigatório"),
});

export type LoginFormValues = z.infer<typeof loginSchema>;
