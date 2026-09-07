import { render, screen, fireEvent } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { MemoryRouter, useLocation } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Sidebar } from "./Sidebar";
import { useAuthStore, type AuthUser } from "@/stores/authStore";

// Detects navigation performed by the shared logout flow (useLogout) without
// mocking react-router: renders alongside the Sidebar inside the same
// MemoryRouter and reports the current pathname.
function LocationDisplay() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname}</div>;
}

function baseUser(permissions: string[]): AuthUser {
  return {
    user_id: 1,
    tenant_id: 1,
    username: "usuario1",
    name: "Usuário Um",
    profile_id: 1,
    profile_name: "Perfil",
    permissions,
  };
}

function renderSidebar(permissions: string[]) {
  useAuthStore.setState({ token: "fake-token", user: baseUser(permissions) });

  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/"]}>
        <Sidebar collapsed={false} onToggle={() => {}} mobileOpen={false} />
        <LocationDisplay />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Sidebar - rodapé fixo (Configurações + Sair)", () => {
  beforeEach(() => {
    useAuthStore.setState({ token: null, user: null });
  });

  afterEach(() => {
    useAuthStore.setState({ token: null, user: null });
  });

  it('mostra "Configurações" no rodapé para usuário com permissão "configuracoes"', () => {
    renderSidebar(["configuracoes"]);
    expect(screen.getByText("Configurações")).toBeInTheDocument();
  });

  it('mostra "Configurações" no rodapé para usuário com permissão "gestao_usuarios"', () => {
    renderSidebar(["gestao_usuarios"]);
    expect(screen.getByText("Configurações")).toBeInTheDocument();
  });

  it('esconde "Configurações" para usuário sem nenhuma das duas permissões, mas mantém "Sair" visível', () => {
    renderSidebar([]);
    expect(screen.queryByText("Configurações")).not.toBeInTheDocument();
    expect(screen.getByText("Sair")).toBeInTheDocument();
  });

  it('usuário só com "gestao_usuarios": expandir "Configurações" mostra só "Usuários", não "Configurações Gerais"', () => {
    renderSidebar(["gestao_usuarios"]);

    // "Configurações Gerais" nunca é renderizado (falta permissão "configuracoes"),
    // independente do accordion estar aberto ou fechado.
    expect(screen.queryByText("Configurações Gerais")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("Configurações"));

    // "Usuários" (permissão "gestao_usuarios") é o único filho renderizado
    // pelo accordion reaproveitado, e "Configurações Gerais" continua ausente.
    expect(screen.getByText("Usuários")).toBeInTheDocument();
    expect(screen.queryByText("Configurações Gerais")).not.toBeInTheDocument();
  });

  it('"Sair" está sempre presente e dispara a função de logout compartilhada ao clicar', () => {
    renderSidebar(["configuracoes"]);

    expect(useAuthStore.getState().token).toBe("fake-token");

    fireEvent.click(screen.getByText("Sair"));

    expect(useAuthStore.getState().token).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
    expect(screen.getByTestId("location")).toHaveTextContent("/login");
  });
});
