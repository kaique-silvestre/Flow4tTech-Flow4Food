import { describe, expect, it } from "vitest";
import { formatCurrency, formatDate, formatQuantidade } from "./format";

describe("formatCurrency", () => {
  it("formats BRL with comma as decimal separator", () => {
    const formatted = formatCurrency(80.1);
    expect(formatted.replace(/\s/g, " ")).toMatch(/R\$\s?80,10/);
  });

  it("handles zero", () => {
    const formatted = formatCurrency(0);
    expect(formatted).toMatch(/R\$/);
    expect(formatted).toMatch(/0,00/);
  });
});

describe("formatDate", () => {
  it("formats date in pt-BR default pattern", () => {
    const d = new Date("2026-05-12T19:34:00");
    const out = formatDate(d);
    expect(out).toBe("12/05/2026 19:34");
  });
});

describe("formatQuantidade", () => {
  it("returns integer without decimals", () => {
    expect(formatQuantidade(3)).toBe("3");
  });

  it("treats 3.000 as integer (no decimals)", () => {
    expect(formatQuantidade(3.000)).toBe("3");
  });

  it("returns fractional with pt-BR decimal separator", () => {
    expect(formatQuantidade(0.25)).toBe("0,25");
  });

  it("returns up to 3 decimal places for fractional (pt-BR)", () => {
    expect(formatQuantidade(0.250)).toBe("0,25");
    expect(formatQuantidade(0.125)).toBe("0,125");
  });

  it("handles zero as integer", () => {
    expect(formatQuantidade(0)).toBe("0");
  });
});
