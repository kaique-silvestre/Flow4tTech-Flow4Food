export type LastEdited = "unitario" | "total";

export interface CalculateLineInput {
  quantidade: number;
  custo_unitario?: number;
  custo_total?: number;
  lastEdited: LastEdited;
}

export interface CalculateLineResult {
  custo_unitario: number;
  custo_total: number;
}

function round2(v: number): number {
  return Math.round(v * 100) / 100;
}

export function calculateLine(input: CalculateLineInput): CalculateLineResult {
  const { quantidade, lastEdited } = input;

  if (lastEdited === "unitario") {
    const unitario = input.custo_unitario ?? 0;
    const total = quantidade > 0 && unitario > 0 ? round2(unitario * quantidade) : 0;
    return { custo_unitario: unitario, custo_total: total };
  } else {
    const total = input.custo_total ?? 0;
    const unitario = quantidade > 0 && total > 0 ? round2(total / quantidade) : 0;
    return { custo_unitario: unitario, custo_total: total };
  }
}
