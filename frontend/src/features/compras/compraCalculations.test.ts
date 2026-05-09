import { describe, expect, it } from "vitest";
import { calculateLine } from "./compraCalculations";

describe("calculateLine", () => {
  it("lastEdited=unitario: custo_total = unitario * quantidade", () => {
    const result = calculateLine({ quantidade: 10, custo_unitario: 2.5, lastEdited: "unitario" });
    expect(result.custo_total).toBe(25.0);
    expect(result.custo_unitario).toBe(2.5);
  });

  it("lastEdited=total: custo_unitario = custo_total / quantidade", () => {
    const result = calculateLine({ quantidade: 10, custo_total: 25, lastEdited: "total" });
    expect(result.custo_unitario).toBe(2.5);
    expect(result.custo_total).toBe(25);
  });

  it("rounds to 2 decimal places (10/3)", () => {
    const result = calculateLine({ quantidade: 3, custo_total: 10, lastEdited: "total" });
    expect(result.custo_unitario).toBe(3.33);
    expect(result.custo_unitario.toString()).not.toContain("3333");
  });

  it("sum of parts with rounding: 10/3 * 3 may not equal exactly 10", () => {
    const result = calculateLine({ quantidade: 3, custo_total: 10, lastEdited: "total" });
    expect(result.custo_unitario).toBe(3.33);
  });

  it("quantidade=0 → custo_total=0 when lastEdited=unitario", () => {
    const result = calculateLine({ quantidade: 0, custo_unitario: 5, lastEdited: "unitario" });
    expect(result.custo_total).toBe(0);
  });

  it("quantidade=0 → custo_unitario=0 when lastEdited=total (no divide by zero)", () => {
    const result = calculateLine({ quantidade: 0, custo_total: 100, lastEdited: "total" });
    expect(result.custo_unitario).toBe(0);
    expect(Number.isFinite(result.custo_unitario)).toBe(true);
  });
});
