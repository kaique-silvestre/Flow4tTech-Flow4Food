import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { GarconsPage } from "./GarconsPage";

// jsdom não implementa a Pointer Events API usada pelo Radix DropdownMenu.
if (typeof window.PointerEvent === "undefined") {
  class PointerEventPolyfill extends MouseEvent {
    pointerId: number;
    pointerType: string;
    constructor(type: string, params: PointerEventInit = {}) {
      super(type, params);
      this.pointerId = params.pointerId ?? 0;
      this.pointerType = params.pointerType ?? "mouse";
    }
  }
  window.PointerEvent = PointerEventPolyfill as unknown as typeof PointerEvent;
}
Element.prototype.hasPointerCapture ??= () => false;
Element.prototype.releasePointerCapture ??= () => {};
Element.prototype.scrollIntoView ??= () => {};

const toggleMutate = vi.fn();

vi.mock("./useGarcons", () => ({
  useGarcons: () => ({
    data: {
      itens: [
        { id: 1, nome: "José da Silva", ativo: true },
        { id: 2, nome: "André Souza", ativo: false },
      ],
    },
    isLoading: false,
  }),
  useToggleGarcomAtivo: () => ({ mutate: toggleMutate, isPending: false }),
}));

vi.mock("./GarcomModal", () => ({
  GarcomModal: () => null,
}));

vi.mock("./GarcomComissoesModal", () => ({
  GarcomComissoesModal: ({ garcom }: { garcom: { nome: string } }) => (
    <div>Comissões de {garcom.nome}</div>
  ),
}));

function renderPage() {
  const client = new QueryClient();
  render(
    <QueryClientProvider client={client}>
      <GarconsPage />
    </QueryClientProvider>,
  );
}

describe("GarconsPage - busca normalizada", () => {
  it("encontra garçom digitando sem acento", () => {
    renderPage();

    const busca = screen.getByPlaceholderText(/buscar/i);
    fireEvent.change(busca, { target: { value: "jose" } });

    expect(screen.getByText("José da Silva")).toBeInTheDocument();
  });

  it("reseta a página para 1 ao digitar na busca", () => {
    renderPage();

    const busca = screen.getByPlaceholderText(/buscar/i);
    fireEvent.change(busca, { target: { value: "x" } });

    expect(screen.getByText("Nenhum garçom encontrado.")).toBeInTheDocument();
  });
});

describe("GarconsPage - dropdown de ações", () => {
  it("abre o modal de comissões ao clicar em Ver Comissões no dropdown", async () => {
    renderPage();

    const trigger = screen.getAllByRole("button", { name: /ações/i })[0];
    fireEvent.pointerDown(trigger, { button: 0, ctrlKey: false });
    fireEvent.click(trigger);
    fireEvent.click(await screen.findByText("Ver Comissões"));

    expect(screen.getByText("Comissões de José da Silva")).toBeInTheDocument();
  });
});
