import { z } from "zod";

export const itemCompraSchema = z.object({
  item_id: z.number().int().positive("Selecione um item"),
  quantidade: z.coerce.number().positive("Quantidade deve ser > 0"),
  custo_total: z.coerce.number().positive("Custo total deve ser > 0"),
});

export const compraSchema = z.object({
  fornecedor_id: z.number().int().positive().optional(),
  data_compra: z.string().min(1, "Data é obrigatória"),
  numero_nota: z.string().optional(),
  itens: z.array(itemCompraSchema).min(1, "Adicione ao menos 1 item"),
});

export type ItemCompraFormValues = z.infer<typeof itemCompraSchema>;
export type CompraFormValues = z.infer<typeof compraSchema>;
