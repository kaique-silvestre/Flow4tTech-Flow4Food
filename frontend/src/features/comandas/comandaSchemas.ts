import { z } from "zod";

export const novaComandaSchema = z.object({
  identificacao: z.string().min(1, "Identificação é obrigatória"),
  tipo_identificacao: z.enum(["nome", "mesa"]),
  garcom_id: z.number().int().positive("Selecione um garçom"),
  pessoas: z.array(z.string().min(1)).default([]),
});

export const lancarItemSchema = z.object({
  item_id: z.number().int().positive(),
  quantidade: z.coerce.number().positive("Quantidade deve ser > 0"),
  pessoa_associada: z.string().optional(),
  observacao: z.string().optional(),
  cortesia: z.boolean().default(false),
});

export const cancelarItemSchema = z.object({
  motivo: z.enum(["cliente_desistiu", "erro_lancamento", "item_indisponivel", "outro"]),
  estornado: z.boolean().default(false),
});

export type NovaComandaValues = z.infer<typeof novaComandaSchema>;
export type LancarItemValues = z.infer<typeof lancarItemSchema>;
export type CancelarItemValues = z.infer<typeof cancelarItemSchema>;
