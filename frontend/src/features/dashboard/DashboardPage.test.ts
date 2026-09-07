import { describe, expect, it } from "vitest";
import { variacao } from "./DashboardPage";

describe("variacao", () => {
  it("returns null when anterior is 0 and atual is not", () => {
    expect(variacao(100, 0)).toBeNull();
  });

  it("returns null when atual and anterior are both 0", () => {
    expect(variacao(0, 0)).toBeNull();
  });

  it("computes percentage change for normal values", () => {
    expect(variacao(150, 100)).toBe(50);
  });

  it("computes negative percentage change", () => {
    expect(variacao(50, 100)).toBe(-50);
  });
});
