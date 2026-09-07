import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { UserModal } from "./UserModal";
import type { UserResponse } from "./useUsers";

let currentUserId = 999;

vi.mock("@/stores/authStore", () => ({
  useAuthStore: (selector: (s: { user: { user_id: number } }) => unknown) =>
    selector({ user: { user_id: currentUserId } }),
}));

vi.mock("./useUsers", async () => {
  const actual = await vi.importActual<typeof import("./useUsers")>("./useUsers");
  return {
    ...actual,
    useCreateUser: () => ({ mutateAsync: vi.fn() }),
    useUpdateUser: () => ({ mutateAsync: vi.fn() }),
    useResetPassword: () => ({ mutate: vi.fn() }),
    useUserPermissions: () => ({ data: [] }),
    useSetUserPermissions: () => ({ mutateAsync: vi.fn() }),
  };
});

vi.mock("./useProfiles", () => ({
  useProfiles: () => ({ data: [] }),
}));

function makeUser(overrides: Partial<UserResponse> = {}): UserResponse {
  return {
    id: 1,
    tenant_id: 1,
    profile_id: null,
    profile_name: "—",
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

function renderModal(user?: UserResponse) {
  const client = new QueryClient();
  render(
    <QueryClientProvider client={client}>
      <UserModal open onClose={() => {}} user={user} />
    </QueryClientProvider>,
  );
}

describe("UserModal - proteções ao editar a si mesmo", () => {
  it("desabilita o campo de Perfil quando o usuário logado edita a si mesmo", () => {
    currentUserId = 1;
    renderModal(makeUser({ id: 1 }));

    const select = screen.getByLabelText(/perfil/i);
    expect(select).toBeDisabled();
    expect(screen.getByText("Você não pode alterar seu próprio perfil")).toBeInTheDocument();
  });

  it("não desabilita o campo de Perfil ao editar outro usuário", () => {
    currentUserId = 999;
    renderModal(makeUser({ id: 1 }));

    const select = screen.getByLabelText(/perfil/i);
    expect(select).not.toBeDisabled();
    expect(screen.queryByText("Você não pode alterar seu próprio perfil")).not.toBeInTheDocument();
  });

  it("desabilita a grade de telas quando o usuário logado edita a si mesmo", () => {
    currentUserId = 1;
    renderModal(makeUser({ id: 1, profile_id: null }));

    const checkboxes = screen.getAllByRole("checkbox").filter((c) => c.id !== "is_active");
    for (const checkbox of checkboxes) {
      expect(checkbox).toBeDisabled();
    }
    expect(screen.getByText("Você não pode alterar suas próprias permissões")).toBeInTheDocument();
  });

  it("não desabilita a grade de telas ao editar outro usuário", () => {
    currentUserId = 999;
    renderModal(makeUser({ id: 1, profile_id: null }));

    const checkboxes = screen.getAllByRole("checkbox").filter((c) => c.id !== "is_active");
    for (const checkbox of checkboxes) {
      expect(checkbox).not.toBeDisabled();
    }
    expect(screen.queryByText("Você não pode alterar suas próprias permissões")).not.toBeInTheDocument();
  });
});
