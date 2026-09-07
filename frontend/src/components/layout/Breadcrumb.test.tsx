import { describe, expect, it } from "vitest";
import { buildCrumbs } from "./Breadcrumb";

describe("buildCrumbs", () => {
  it("returns no breadcrumb for a root item with no deeper route", () => {
    expect(buildCrumbs("/cardapio", undefined)).toEqual([]);
  });

  it("returns only the parent label when a deeper route has no dynamic label yet", () => {
    expect(buildCrumbs("/cardapio/5", undefined)).toEqual([{ label: "Cardápio" }]);
  });

  it("returns parent + dynamic label when a deeper route has a label", () => {
    expect(buildCrumbs("/cardapio/5", "X-Burger")).toEqual([
      { label: "Cardápio", to: "/cardapio" },
      { label: "X-Burger" },
    ]);
  });

  it("keeps static children groups working (e.g. Estoque > Movimentos)", () => {
    expect(buildCrumbs("/estoque/movimentos", "should be ignored")).toEqual([
      { label: "Estoque" },
      { label: "Movimentos", to: "/estoque/movimentos" },
    ]);
  });

  it("collapses redundant group/child labels (e.g. Compras > Compras)", () => {
    expect(buildCrumbs("/compras", undefined)).toEqual([{ label: "Compras" }]);
  });

  it("returns no breadcrumb for an unmatched route", () => {
    expect(buildCrumbs("/does-not-exist", undefined)).toEqual([]);
  });
});
