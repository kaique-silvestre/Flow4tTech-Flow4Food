import { z } from "zod";

export const fichaTecnicaItemSchema = z.object({
  insumo_id: z.number({ required_error: "Selecione um insumo" }).min(1),
  quantidade: z
    .string()
    .min(1, "Obrigatório")
    .refine((v) => !isNaN(Number(v)) && Number(v) > 0, "Deve ser > 0"),
});

export const produtoSchema = z.object({
  nome: z.string().min(1, "Obrigatório"),
  categoria_id: z
    .number({ required_error: "Selecione uma categoria", invalid_type_error: "Selecione uma categoria" })
    .min(1, "Selecione uma categoria"),
  preco_venda: z
    .string()
    .optional()
    .refine((v) => !v || (!isNaN(Number(v)) && Number(v) >= 0), "Valor inválido"),
  ficha_tecnica: z.array(fichaTecnicaItemSchema).optional(),
});

export type ProdutoFormValues = z.infer<typeof produtoSchema>;
