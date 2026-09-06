import { describe, expect, it } from "vitest";
import { aplicarDescontoSchema } from "./fechamentoSchemas";

describe("aplicarDescontoSchema", () => {
  it("accepts a percentual discount within 0-100", () => {
    const result = aplicarDescontoSchema.safeParse({ tipo: "percentual", valor: 50 });
    expect(result.success).toBe(true);
  });

  it("accepts exactly 100% (backend limit is ge=0, le=100)", () => {
    const result = aplicarDescontoSchema.safeParse({ tipo: "percentual", valor: 100 });
    expect(result.success).toBe(true);
  });

  it("rejects a percentual discount above 100, mirroring the backend Field(le=100)", () => {
    const result = aplicarDescontoSchema.safeParse({ tipo: "percentual", valor: 150 });
    expect(result.success).toBe(false);
  });

  it("does not cap a fixed R$ discount at 100", () => {
    const result = aplicarDescontoSchema.safeParse({ tipo: "valor", valor: 500 });
    expect(result.success).toBe(true);
  });
});
