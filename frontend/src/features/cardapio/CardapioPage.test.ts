import { describe, expect, it } from "vitest";
import { normalizarTexto } from "./CardapioPage";

describe("normalizarTexto", () => {
  it("removes accents so 'agua' matches 'Água'", () => {
    expect(normalizarTexto("Água Com Gás 500ml").includes(normalizarTexto("agua"))).toBe(true);
  });

  it("ignores case so 'AGUA' matches 'Água'", () => {
    expect(normalizarTexto("Água Com Gás 500ml").includes(normalizarTexto("AGUA"))).toBe(true);
  });

  it("does not match unrelated terms", () => {
    expect(normalizarTexto("Refrigerante Cola").includes(normalizarTexto("agua"))).toBe(false);
  });
});
