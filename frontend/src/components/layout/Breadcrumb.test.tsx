import { describe, expect, it } from "vitest";
import { buildCrumbs } from "./Breadcrumb";

const TENANT = "Empresa";

describe("buildCrumbs", () => {
  it("returns tenant + page label for a root route (e.g. Dashboard)", () => {
    expect(buildCrumbs("/", TENANT)).toEqual([{ label: TENANT }, { label: "Dashboard" }]);
  });

  it("returns tenant + page label for a top-level item with no children (e.g. Cardápio)", () => {
    expect(buildCrumbs("/cardapio", TENANT)).toEqual([{ label: TENANT }, { label: "Cardápio" }]);
  });

  it("returns exactly 2 segments for a group's subitem, dropping the parent group (e.g. Estoque > Movimentos)", () => {
    expect(buildCrumbs("/estoque/movimentos", TENANT)).toEqual([
      { label: TENANT },
      { label: "Movimentos" },
    ]);
  });

  it("collapses redundant group/child labels (e.g. Compras > Compras) into tenant + single label", () => {
    expect(buildCrumbs("/compras", TENANT)).toEqual([{ label: TENANT }, { label: "Compras" }]);
  });

  it("falls back to the parent item label on a deeper route with no dynamic label yet", () => {
    expect(buildCrumbs("/cardapio/5", TENANT)).toEqual([{ label: TENANT }, { label: "Cardápio" }]);
  });

  it("uses the dynamic label on a deeper route once it's available", () => {
    expect(buildCrumbs("/cardapio/5", TENANT, "X-Burger")).toEqual([
      { label: TENANT },
      { label: "X-Burger" },
    ]);
  });

  it("returns only the tenant name (1 segment) for an unrecognized route, never an invented label", () => {
    expect(buildCrumbs("/does-not-exist", TENANT)).toEqual([{ label: TENANT }]);
  });
});
