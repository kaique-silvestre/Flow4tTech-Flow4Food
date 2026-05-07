import { z } from "zod";

export const componenteSchema = z.object({
  insumo_id: z.number().int().positive("Selecione um insumo"),
  quantidade: z.coerce.number().positive("Quantidade deve ser > 0"),
});

export const itemSchema = z.object({
  nome: z.string().min(1, "Nome é obrigatório"),
  categoria_id: z.number().int().nullable().optional(),
  tipo: z.enum(["simples", "composto"]),
  vendavel: z.boolean(),
  unidade_base: z.enum(["un", "g"]),
  quantidade_caixa: z.coerce.number().int().positive().nullable().optional(),
  preco_venda: z.coerce.number().positive().nullable().optional(),
  ficha_tecnica: z.array(componenteSchema).optional(),
});

export type ItemFormValues = z.infer<typeof itemSchema>;
export type ComponenteFormValues = z.infer<typeof componenteSchema>;
