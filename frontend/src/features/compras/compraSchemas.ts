import { z } from "zod";

export const itemCompraSchema = z.object({
  item_id: z.number().int().positive("Selecione um item"),
  quantidade: z.coerce.number().positive("Quantidade deve ser > 0"),
  custo_total: z.coerce.number().positive("Custo total deve ser > 0"),
});

export const compraSchema = z
  .object({
    fornecedor_id: z.number().int().positive().optional(),
    data_compra: z.string().min(1, "Data é obrigatória"),
    numero_nota: z.string().optional(),
    tipo_compra: z.enum(["imediata", "agendada", "a_prazo"]).default("imediata"),
    data_prevista_recebimento: z.string().optional(),
    data_prevista_pagamento: z.string().optional(),
    itens: z.array(itemCompraSchema).min(1, "Adicione ao menos 1 item"),
  })
  .superRefine((val, ctx) => {
    if (val.tipo_compra === "agendada" && !val.data_prevista_recebimento) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["data_prevista_recebimento"],
        message: "Data prevista de recebimento é obrigatória",
      });
    }
    if ((val.tipo_compra === "agendada" || val.tipo_compra === "a_prazo") && !val.data_prevista_pagamento) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["data_prevista_pagamento"],
        message: "Data de vencimento do pagamento é obrigatória",
      });
    }
  });

export type ItemCompraFormValues = z.infer<typeof itemCompraSchema>;
export type CompraFormValues = z.infer<typeof compraSchema>;
