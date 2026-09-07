import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { GestaoUsuariosPage } from "./GestaoUsuariosPage";
import type { UserResponse } from "./useUsers";
import type { ProfileResponse } from "./useProfiles";

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

let users: UserResponse[] = [];
let profiles: ProfileResponse[] = [];
const toggleUserMutate = vi.fn();
const toggleProfileMutate = vi.fn();
let currentUserId = 999;

vi.mock("@/stores/authStore", () => ({
  useAuthStore: (selector: (s: { user: { user_id: number } }) => unknown) =>
    selector({ user: { user_id: currentUserId } }),
}));

vi.mock("./useUsers", () => ({
  useUsers: () => ({ data: users, isLoading: false, isError: false }),
  useToggleUserActive: () => ({ mutate: toggleUserMutate, isPending: false }),
}));

vi.mock("./useProfiles", () => ({
  useProfiles: () => ({ data: profiles }),
  useToggleProfileActive: () => ({ mutate: toggleProfileMutate, isPending: false }),
}));

vi.mock("./UserModal", () => ({ UserModal: () => null }));
vi.mock("./ProfileModal", () => ({ ProfileModal: () => null }));

// Radix Dialog e Radix DropdownMenu disputam foco quando um item de menu
// abre um diálogo no mesmo tick, o que trava em jsdom (sem afetar o browser
// real). Substituímos o ConfirmDialog compartilhado por uma versão simples
// só para exercitar a lógica de wiring da página (título/ação/mutation).
vi.mock("@/components/ui/confirm-dialog", () => ({
  ConfirmDialog: ({
    open,
    title,
    confirmLabel,
    onConfirm,
  }: {
    open: boolean;
    title: string;
    confirmLabel?: string;
    onConfirm: () => void;
  }) =>
    open ? (
      <div>
        <p>{title}</p>
        <button onClick={onConfirm}>{confirmLabel ?? "Confirmar"}</button>
      </div>
    ) : null,
}));

function makeUser(overrides: Partial<UserResponse> = {}): UserResponse {
  return {
    id: 1,
    tenant_id: 1,
    profile_id: 1,
    profile_name: "Garçom",
    name: "José da Silva",
    username: "jose",
    email: "jose@example.com",
    is_active: true,
    is_owner: false,
    last_login: null,
    created_at: "",
    ...overrides,
  };
}

function makeProfile(overrides: Partial<ProfileResponse> = {}): ProfileResponse {
  return {
    id: 1,
    tenant_id: 1,
    name: "Garçom",
    description: null,
    is_system: false,
    is_active: true,
    template_id: null,
    permissions: [],
    user_count: 0,
    created_at: "",
    ...overrides,
  };
}

function renderPage() {
  const client = new QueryClient();
  render(
    <QueryClientProvider client={client}>
      <GestaoUsuariosPage />
    </QueryClientProvider>,
  );
}

async function openRowMenu(rowText: string) {
  const row = screen.getByText(rowText).closest("tr")!;
  const trigger = within(row).getByRole("button", { name: /ações/i });
  fireEvent.pointerDown(trigger, { button: 0, ctrlKey: false });
  fireEvent.click(trigger);
  return row;
}

describe("GestaoUsuariosPage - dropdown de ações de Usuário", () => {
  it("mostra itens Editar e Desativar para usuário comum ativo", async () => {
    users = [makeUser({ is_active: true })];
    currentUserId = 999;
    renderPage();

    await openRowMenu("José da Silva");

    expect(await screen.findByText("Editar")).toBeInTheDocument();
    expect(screen.getByText("Desativar")).toBeInTheDocument();
  });

  it("mostra Ativar quando usuário está inativo", async () => {
    users = [makeUser({ is_active: false })];
    currentUserId = 999;
    renderPage();

    fireEvent.click(screen.getByLabelText(/mostrar inativos/i));
    await openRowMenu("José da Silva");

    expect(await screen.findByText("Ativar")).toBeInTheDocument();
  });

  it("não mostra Desativar quando o usuário é o próprio usuário logado", async () => {
    users = [makeUser({ id: 42, is_active: true })];
    currentUserId = 42;
    renderPage();

    await openRowMenu("José da Silva");

    await screen.findByText("Editar");
    expect(screen.queryByText("Desativar")).not.toBeInTheDocument();
  });

  it("não mostra Desativar quando o usuário é proprietário", async () => {
    users = [makeUser({ is_owner: true, is_active: true })];
    currentUserId = 999;
    renderPage();

    await openRowMenu("José da Silva");

    await screen.findByText("Editar");
    expect(screen.queryByText("Desativar")).not.toBeInTheDocument();
  });

  it("abre confirmação e dispara mutation ao clicar em Desativar", async () => {
    users = [makeUser({ is_active: true })];
    currentUserId = 999;
    renderPage();

    await openRowMenu("José da Silva");
    fireEvent.click(await screen.findByText("Desativar"));

    expect(await screen.findByText('Desativar "José da Silva"?')).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Desativar" }));

    expect(toggleUserMutate).toHaveBeenCalledWith(1);
  });
});

describe("GestaoUsuariosPage - dropdown de ações de Perfil", () => {
  it("mostra item Editar para perfil não-Admin e permite Desativar", async () => {
    users = [];
    profiles = [makeProfile({ name: "Garçom", user_count: 0 })];
    renderPage();
    fireEvent.click(screen.getByRole("button", { name: "Perfis" }));

    await openRowMenu("Garçom");

    const editItem = await screen.findByText("Editar");
    expect(editItem).toBeInTheDocument();
    const toggleItem = screen.getByText("Desativar");
    expect(toggleItem.closest('[role="menuitem"]')).not.toHaveAttribute("data-disabled");
  });

  it("mostra item Ver e Desativar desabilitado para perfil Admin", async () => {
    users = [];
    profiles = [makeProfile({ name: "Admin", user_count: 3 })];
    renderPage();
    fireEvent.click(screen.getByRole("button", { name: "Perfis" }));

    await openRowMenu("Admin");

    expect(await screen.findByText("Ver")).toBeInTheDocument();
    const toggleItem = screen.getByText("Desativar");
    expect(toggleItem.closest('[role="menuitem"]')).toHaveAttribute("data-disabled");
  });

  it("desabilita Desativar quando perfil tem usuários vinculados", async () => {
    users = [];
    profiles = [makeProfile({ name: "Garçom", user_count: 2 })];
    renderPage();
    fireEvent.click(screen.getByRole("button", { name: "Perfis" }));

    await openRowMenu("Garçom");

    const toggleItem = await screen.findByText("Desativar");
    expect(toggleItem.closest('[role="menuitem"]')).toHaveAttribute("data-disabled");
  });

  it("não dispara mutation ao clicar em Desativar desabilitado (perfil com usuários vinculados)", async () => {
    users = [];
    profiles = [makeProfile({ id: 9, name: "Garçom", user_count: 2 })];
    renderPage();
    fireEvent.click(screen.getByRole("button", { name: "Perfis" }));

    await openRowMenu("Garçom");
    fireEvent.click(await screen.findByText("Desativar"));

    expect(screen.queryByText('Desativar perfil "Garçom"?')).not.toBeInTheDocument();
    expect(toggleProfileMutate).not.toHaveBeenCalled();
  });

  it("dispara mutation ao clicar em Desativar/Ativar quando habilitado", async () => {
    users = [];
    profiles = [makeProfile({ id: 7, name: "Garçom", user_count: 0, is_active: true })];
    renderPage();
    fireEvent.click(screen.getByRole("button", { name: "Perfis" }));

    await openRowMenu("Garçom");
    fireEvent.click(await screen.findByText("Desativar"));

    expect(await screen.findByText('Desativar perfil "Garçom"?')).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Desativar" }));

    expect(toggleProfileMutate).toHaveBeenCalledWith(7);
  });
});
