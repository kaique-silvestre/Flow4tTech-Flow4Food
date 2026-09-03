import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { platformApi, usePlatformCockpit, useTenants } from "./usePlatformApi";

function wrapper({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>{children}</QueryClientProvider>;
}

describe("platform pagination hooks", () => {
  it("requests tenants as a server-side page", async () => {
    const get = vi.spyOn(platformApi, "get").mockResolvedValue({ data: { items: [], total: 101, page: 2, page_size: 50, total_pages: 3 } });
    const { result } = renderHook(() => useTenants("ativa", 2, 50), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(get).toHaveBeenCalledWith(expect.stringContaining("/api/platform/tenants"), expect.objectContaining({ params: { status: "ativa", page: 2, page_size: 50 } }));
    expect(result.current.data?.total_pages).toBe(3);
  });

  it("requests cockpit as a server-side page", async () => {
    const get = vi.spyOn(platformApi, "get").mockResolvedValue({ data: { items: [], total: 51, page: 2, page_size: 50, total_pages: 2 } });
    const { result } = renderHook(() => usePlatformCockpit(undefined, 2, 50), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(get).toHaveBeenCalledWith(expect.stringContaining("/api/platform/cockpit"), expect.objectContaining({ params: { page: 2, page_size: 50 } }));
    expect(result.current.data?.items).toEqual([]);
  });
});
