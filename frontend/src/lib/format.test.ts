import { describe, expect, it } from "vitest";
import { formatCurrency, formatDate } from "./format";

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
