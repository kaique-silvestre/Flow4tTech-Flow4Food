import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MovimentosPage } from "./MovimentosPage";

vi.mock("./useEstoque", () => ({
  useSaldoEstoque: () => ({ data: { itens: [] } }),
  useMovimentos: () => ({
    data: { itens: [], total: 0, pagina: 1, por_pagina: 15 },
    isLoading: false,
    isError: false,
  }),
  useMovimentosProdutos: () => ({
    data: { itens: [], total: 0, pagina: 1, por_pagina: 15 },
    isLoading: false,
    isError: false,
  }),
}));

vi.mock("@/features/cadastros/produtos/useProdutos", () => ({
  useProdutos: () => ({ data: { itens: [] } }),
}));

function renderPage(initialPath: string) {
  const router = createMemoryRouter(
    [{ path: "/estoque/movimentos", element: <MovimentosPage /> }],
    { initialEntries: [initialPath] },
  );
  const client = new QueryClient();
  render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return router;
}

describe("MovimentosPage - aba ativa via query param", () => {
  it("usa a aba Insumos por padrão quando não há query param", () => {
    renderPage("/estoque/movimentos");
    expect(screen.getByText("Nenhum movimento encontrado.")).toBeInTheDocument();
  });

  it("carrega a aba Produtos ao abrir com ?tab=produtos", () => {
    renderPage("/estoque/movimentos?tab=produtos");
    expect(screen.getByText("Nenhuma saída de produto encontrada.")).toBeInTheDocument();
  });

  it("atualiza o query param ao trocar de aba, sem adicionar filtros na URL", () => {
    const router = renderPage("/estoque/movimentos");

    fireEvent.click(screen.getByText("Produtos"));

    expect(router.state.location.pathname + router.state.location.search).toBe(
      "/estoque/movimentos?tab=produtos",
    );
    expect(screen.getByText("Nenhuma saída de produto encontrada.")).toBeInTheDocument();
  });
});
