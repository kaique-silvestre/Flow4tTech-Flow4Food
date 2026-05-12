export interface UnitOption {
  value: string;
  label: string;
  factor: number; // multiply input by this to get base unit quantity
}

const FAMILIES: Record<string, { alt: string; altFactor: number }> = {
  kg: { alt: "g",  altFactor: 0.001 },
  g:  { alt: "kg", altFactor: 1000  },
};

export function getFamilyOptions(
  unidadeBase: string,
  quantidadeCaixa?: number | null
): UnitOption[] {
  const base: UnitOption = { value: unidadeBase, label: unidadeBase, factor: 1 };
  const family = FAMILIES[unidadeBase];
  if (family) {
    return [base, { value: family.alt, label: family.alt, factor: family.altFactor }];
  }
  if (quantidadeCaixa && quantidadeCaixa > 0) {
    return [
      base,
      { value: "cx", label: `cx (${quantidadeCaixa} ${unidadeBase})`, factor: quantidadeCaixa },
    ];
  }
  return [base];
}

export function toBase(value: number, option: UnitOption): number {
  return value * option.factor;
}
