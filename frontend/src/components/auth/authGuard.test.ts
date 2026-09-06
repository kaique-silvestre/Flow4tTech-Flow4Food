import { describe, expect, it, vi } from "vitest";
import { resolveAuthGuard } from "./authGuard";

describe("resolveAuthGuard", () => {
  it("denies access when there is no token and no bypass", () => {
    const clearToken = vi.fn();
    const allowed = resolveAuthGuard({ token: null, user: null, clearToken });
    expect(allowed).toBe(false);
    expect(clearToken).not.toHaveBeenCalled();
  });

  it("allows access when there is no token but a bypass session exists (impersonation)", () => {
    const clearToken = vi.fn();
    const allowed = resolveAuthGuard({ token: null, user: null, clearToken }, true);
    expect(allowed).toBe(true);
    expect(clearToken).not.toHaveBeenCalled();
  });

  it("clears the token and denies access when the token failed to decode into a user", () => {
    const clearToken = vi.fn();
    const allowed = resolveAuthGuard({ token: "malformed", user: null, clearToken });
    expect(allowed).toBe(false);
    expect(clearToken).toHaveBeenCalledTimes(1);
  });

  it("does not clear the token when a bypass session is active, even without a decoded user", () => {
    const clearToken = vi.fn();
    const allowed = resolveAuthGuard({ token: null, user: null, clearToken }, true);
    expect(allowed).toBe(true);
    expect(clearToken).not.toHaveBeenCalled();
  });

  it("allows access when both token and user are present", () => {
    const clearToken = vi.fn();
    const allowed = resolveAuthGuard({ token: "abc", user: { id: 1 }, clearToken });
    expect(allowed).toBe(true);
    expect(clearToken).not.toHaveBeenCalled();
  });
});
