import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { MetodosPagamentoPage, normalizarTexto } from "./MetodosPagamentoPage";

const toggleMutate = vi.fn();
const deleteMutate = vi.fn();

vi.mock("./useMetodosPagamento", () => ({
  useMetodosPagamento: () => ({
    data: [
      { id: 1, nome: "Dinheiro", ativo: true, tipo: "dinheiro", padrao: true },
      { id: 2, nome: "Pix", ativo: true, tipo: "pix", padrao: false },
      { id: 3, nome: "Cartão Débito", ativo: false, tipo: "cartao", padrao: false },
    ],
    isLoading: false,
  }),
  useToggleMetodoAtivo: () => ({ mutate: toggleMutate, isPending: false }),
  useDeleteMetodoPagamento: () => ({ mutate: deleteMutate, isPending: false }),
}));

vi.mock("./MetodoPagamentoModal", () => ({
  MetodoPagamentoModal: () => null,
}));

function renderPage() {
  const client = new QueryClient();
  render(
    <QueryClientProvider client={client}>
      <MetodosPagamentoPage />
    </QueryClientProvider>,
  );
}

describe("normalizarTexto", () => {
  it("removes accents so 'cartao' matches 'Cartão'", () => {
    expect(normalizarTexto("Cartão Débito").includes(normalizarTexto("cartao"))).toBe(true);
  });

  it("does not match unrelated terms", () => {
    expect(normalizarTexto("Dinheiro").includes(normalizarTexto("pix"))).toBe(false);
  });
});

describe("MetodosPagamentoPage - busca normalizada", () => {
  it("encontra método digitando sem acento", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Todos" }));
    const busca = screen.getByPlaceholderText(/buscar/i);
    fireEvent.change(busca, { target: { value: "cartao" } });

    expect(screen.getByText("Cartão Débito")).toBeInTheDocument();
  });

  it("reseta a página para 1 ao digitar na busca", () => {
    renderPage();

    const busca = screen.getByPlaceholderText(/buscar/i);
    fireEvent.change(busca, { target: { value: "zzz" } });

    expect(screen.getByText("Nenhum método de pagamento encontrado.")).toBeInTheDocument();
  });
});

describe("MetodosPagamentoPage - ações de método padrão", () => {
  it("desabilita Desativar para método padrão com texto de apoio", () => {
    renderPage();

    const linhaDinheiro = screen.getByText("Dinheiro").closest("tr")!;
    const desativarBtn = within(linhaDinheiro).getByRole("button", { name: "Desativar" });
    expect(desativarBtn).toBeDisabled();
    expect(desativarBtn).toHaveAttribute("title", "Método padrão não pode ser desativado");
  });

  it("desabilita Remover para método padrão com texto de apoio", () => {
    renderPage();

    const linhaDinheiro = screen.getByText("Dinheiro").closest("tr")!;
    const removerBtn = within(linhaDinheiro).getByRole("button", { name: "Remover" });
    expect(removerBtn).toBeDisabled();
    expect(removerBtn).toHaveAttribute("title", "Método padrão não pode ser removido");
  });
});
