import { LayoutDashboard } from "lucide-react";
import { describe, expect, it } from "vitest";
import { filterNavItems, type NavGroup } from "./navConfig";

// SubNavItem.icon is required by the type, so every mock child carries a
// (visually irrelevant) icon just to satisfy the shape — these tests only
// exercise label matching, never rendering.
const ICON = LayoutDashboard;

const GROUPS: NavGroup[] = [
  {
    items: [
      { label: "Dashboard", to: "/" },
      { label: "Calendário", to: "/calendario" },
    ],
  },
  {
    heading: "Operação",
    items: [
      { label: "Cardápio", to: "/cardapio" },
      {
        label: "Vendas",
        to: null,
        children: [
          { label: "Comandas", to: "/vendas/comandas", icon: ICON },
          { label: "Consumo Interno", to: "/consumo-interno", icon: ICON },
        ],
      },
      {
        label: "Estoque",
        to: null,
        children: [
          { label: "Estoque", to: "/estoque", icon: ICON },
          { label: "Movimentos", to: "/estoque/movimentos", icon: ICON },
        ],
      },
    ],
  },
];

describe("filterNavItems", () => {
  it("returns everything unchanged for an empty query", () => {
    expect(filterNavItems("", GROUPS)).toEqual(GROUPS);
  });

  it("returns everything unchanged for a whitespace-only query", () => {
    expect(filterNavItems("   ", GROUPS)).toEqual(GROUPS);
  });

  it("keeps a top-level item that matches by label, dropping non-matching items in the same group", () => {
    const result = filterNavItems("dashboard", GROUPS);
    expect(result).toEqual([{ items: [{ label: "Dashboard", to: "/" }] }]);
  });

  it("keeps a parent whose child matches, showing only the matching children", () => {
    const result = filterNavItems("comandas", GROUPS);
    expect(result).toEqual([
      {
        heading: "Operação",
        items: [
          {
            label: "Vendas",
            to: null,
            children: [{ label: "Comandas", to: "/vendas/comandas", icon: ICON }],
          },
        ],
      },
    ]);
  });

  it("shows every child of a matching parent when the parent label itself matches (not just search-matched children)", () => {
    const result = filterNavItems("estoque", GROUPS);
    expect(result).toEqual([
      {
        heading: "Operação",
        items: [
          {
            label: "Estoque",
            to: null,
            children: [
              { label: "Estoque", to: "/estoque", icon: ICON },
              { label: "Movimentos", to: "/estoque/movimentos", icon: ICON },
            ],
          },
        ],
      },
    ]);
  });

  it("is case-insensitive", () => {
    expect(filterNavItems("DaShBoArD", GROUPS)).toEqual(filterNavItems("dashboard", GROUPS));
    expect(filterNavItems("COMANDAS", GROUPS)).toEqual(filterNavItems("comandas", GROUPS));
  });

  it("returns an empty list (groups dropped entirely) when nothing matches", () => {
    expect(filterNavItems("xyz-inexistente", GROUPS)).toEqual([]);
  });

  it("drops a group with a heading entirely once none of its items match", () => {
    const result = filterNavItems("dashboard", GROUPS);
    expect(result.some((g) => g.heading === "Operação")).toBe(false);
  });
});
