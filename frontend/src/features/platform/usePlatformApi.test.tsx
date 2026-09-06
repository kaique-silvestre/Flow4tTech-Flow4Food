import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { platformApi, usePlatformCockpit, useTenants, useUpdateTenantWithAssinatura } from "./usePlatformApi";

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

describe("useUpdateTenantWithAssinatura", () => {
  it("only patches tenant data when subscription status/vencimento are unchanged", async () => {
    const patch = vi.spyOn(platformApi, "patch").mockResolvedValue({ data: {} });
    const { result } = renderHook(() => useUpdateTenantWithAssinatura(), { wrapper });

    act(() => {
      result.current.mutate({
        tenantId: 1,
        nome_fantasia: "Nova Razão Social",
        currentStatus: "ativa",
        status: "ativa",
        data_vencimento: "",
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(patch).toHaveBeenCalledTimes(1);
    expect(patch).toHaveBeenCalledWith(expect.stringContaining("/api/platform/tenants/1"), expect.objectContaining({ nome_fantasia: "Nova Razão Social" }));
  });

  it("also patches the subscription when status changed", async () => {
    const patch = vi.spyOn(platformApi, "patch").mockResolvedValue({ data: {} });
    const { result } = renderHook(() => useUpdateTenantWithAssinatura(), { wrapper });

    act(() => {
      result.current.mutate({
        tenantId: 2,
        currentStatus: "ativa",
        status: "suspensa",
        data_vencimento: "",
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(patch).toHaveBeenCalledTimes(2);
    expect(patch).toHaveBeenCalledWith(
      expect.stringContaining("/api/platform/tenants/2/assinatura/full"),
      expect.objectContaining({ status: "suspensa" })
    );
  });

  it("also patches the subscription when a new data_vencimento is set, even if status is unchanged", async () => {
    const patch = vi.spyOn(platformApi, "patch").mockResolvedValue({ data: {} });
    const { result } = renderHook(() => useUpdateTenantWithAssinatura(), { wrapper });

    act(() => {
      result.current.mutate({
        tenantId: 3,
        currentStatus: "trial",
        status: "trial",
        data_vencimento: "2026-12-01T00:00",
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(patch).toHaveBeenCalledTimes(2);
  });
});
