import { describe, expect, it } from "vitest";
import { normalizarTexto } from "./InsumosPage";

describe("normalizarTexto", () => {
  it("removes accents so 'agua' matches 'Água'", () => {
    expect(normalizarTexto("Água Mineral").includes(normalizarTexto("agua"))).toBe(true);
  });

  it("ignores case so 'AGUA' matches 'Água'", () => {
    expect(normalizarTexto("Água Mineral").includes(normalizarTexto("AGUA"))).toBe(true);
  });

  it("does not match unrelated terms", () => {
    expect(normalizarTexto("Farinha de Trigo").includes(normalizarTexto("agua"))).toBe(false);
  });
});
