import { z } from "zod";

export const motivoPerdaOptions = [
  { value: "perda", label: "Perda" },
  { value: "quebra", label: "Quebra" },
  { value: "cortesia", label: "Cortesia" },
  { value: "outro", label: "Outro" },
] as const;

export const baixaSemVendaSchema = z.object({
  item_id: z.number().int().positive("Selecione um item"),
  quantidade: z.coerce.number().positive("Quantidade deve ser > 0"),
  motivo: z.enum(["perda", "quebra", "cortesia", "outro"]),
  observacao: z.string().optional(),
});

export type BaixaSemVendaFormValues = z.infer<typeof baixaSemVendaSchema>;
