import { z } from "zod";

export const loginSchema = z.object({
  identifier: z.string().min(1, "Campo obrigatório"),
  password: z.string().min(1, "Campo obrigatório"),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

export const forgotPasswordSchema = z.object({
  email: z.string().email("Email inválido"),
});

export type ForgotPasswordValues = z.infer<typeof forgotPasswordSchema>;

export const resetPasswordSchema = z
  .object({
    new_password: z.string().min(6, "Mínimo 6 caracteres"),
    confirm_password: z.string().min(1, "Campo obrigatório"),
  })
  .refine((d) => d.new_password === d.confirm_password, {
    message: "Senhas não coincidem",
    path: ["confirm_password"],
  });

export type ResetPasswordValues = z.infer<typeof resetPasswordSchema>;
