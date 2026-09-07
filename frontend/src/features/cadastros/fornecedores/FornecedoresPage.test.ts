import { describe, expect, it } from "vitest";
import { normalizarTexto } from "./FornecedoresPage";

describe("normalizarTexto", () => {
  it("removes accents so 'agua' matches 'Água'", () => {
    expect(normalizarTexto("Água Distribuidora").includes(normalizarTexto("agua"))).toBe(true);
  });

  it("ignores case so 'AGUA' matches 'Água'", () => {
    expect(normalizarTexto("Água Distribuidora").includes(normalizarTexto("AGUA"))).toBe(true);
  });

  it("does not match unrelated terms", () => {
    expect(normalizarTexto("Frigorífico Central").includes(normalizarTexto("agua"))).toBe(false);
  });
});
