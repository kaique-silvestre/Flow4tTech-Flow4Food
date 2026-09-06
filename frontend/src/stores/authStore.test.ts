import { beforeEach, describe, expect, it, vi } from "vitest";
import { queryClient } from "@/lib/queryClient";
import { useAuthStore } from "./authStore";

function makeToken(payload: Record<string, unknown>): string {
  const base64 = btoa(JSON.stringify(payload)).replace(/\+/g, "-").replace(/\//g, "_");
  return `header.${base64}.signature`;
}

describe("useAuthStore", () => {
  beforeEach(() => {
    useAuthStore.getState().clearToken();
    queryClient.clear();
  });

  it("clears the shared TanStack Query cache when a new token is set (login)", () => {
    queryClient.setQueryData(["comandas"], [{ id: 1 }]);
    expect(queryClient.getQueryData(["comandas"])).toBeDefined();

    const token = makeToken({ user_id: 1, tenant_id: 1, permissions: [] });
    useAuthStore.getState().setToken(token);

    expect(queryClient.getQueryData(["comandas"])).toBeUndefined();
  });

  it("clears the shared TanStack Query cache on logout", () => {
    const token = makeToken({ user_id: 1, tenant_id: 1, permissions: [] });
    useAuthStore.getState().setToken(token);
    queryClient.setQueryData(["comandas"], [{ id: 1 }]);
    expect(queryClient.getQueryData(["comandas"])).toBeDefined();

    useAuthStore.getState().clearToken();

    expect(queryClient.getQueryData(["comandas"])).toBeUndefined();
    expect(useAuthStore.getState().token).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
  });

  it("clear on next login prevents the previous user's cached data from leaking", () => {
    const tokenA = makeToken({ user_id: 1, tenant_id: 1, permissions: [] });
    useAuthStore.getState().setToken(tokenA);
    queryClient.setQueryData(["comandas"], [{ id: 999, identificacao: "user-a-data" }]);

    const clearSpy = vi.spyOn(queryClient, "clear");
    const tokenB = makeToken({ user_id: 2, tenant_id: 2, permissions: [] });
    useAuthStore.getState().setToken(tokenB);

    expect(clearSpy).toHaveBeenCalled();
    expect(queryClient.getQueryData(["comandas"])).toBeUndefined();
    clearSpy.mockRestore();
  });
});
