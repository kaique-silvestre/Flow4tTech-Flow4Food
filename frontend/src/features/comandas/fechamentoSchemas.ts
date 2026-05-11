import { z } from "zod";

export const aplicarDescontoSchema = z
  .object({
    tipo: z.enum(["percentual", "valor"]),
    valor: z.coerce.number().positive("Valor deve ser positivo"),
  })
  .refine((d) => d.valor > 0, { message: "Informe um valor de desconto", path: ["valor"] });

export type AplicarDescontoValues = z.infer<typeof aplicarDescontoSchema>;

export const pagamentoSchema = z.object({
  metodo_id: z.number().int().positive("Selecione um método"),
  valor: z.coerce.number().positive("Valor deve ser positivo"),
});

export const fecharComandaSchema = z.object({
  pagamentos: z.array(pagamentoSchema),
  modo_divisao: z.enum(["sem_divisao", "igualmente", "por_pessoa", "parcial"]),
});

export type FecharComandaValues = z.infer<typeof fecharComandaSchema>;
