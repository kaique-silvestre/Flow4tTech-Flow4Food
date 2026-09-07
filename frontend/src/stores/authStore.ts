import { create } from "zustand";
import { persist } from "zustand/middleware";
import { queryClient } from "@/lib/queryClient";
import { decodeJwtPayload } from "@/lib/jwt";

export interface AuthUser {
  user_id: number;
  tenant_id: number;
  username: string;
  name: string;
  profile_id: number;
  profile_name: string;
  permissions: string[];
  subscription_status?: string;
  /** Nome da empresa (tenant), presente a partir da ticket 01 (tenant_name no JWT).
   * Opcional para não quebrar tokens antigos, emitidos antes dessa mudança. */
  tenant_name?: string;
}

function parseJwtPayload(token: string): AuthUser | null {
  const payload = decodeJwtPayload<AuthUser>(token);
  if (!payload || !Array.isArray(payload.permissions)) return null;
  return payload;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  setToken: (t: string) => void;
  clearToken: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setToken: (t) => {
        // A PDV compartilhado pode ter outro usuário logado antes — sem isso,
        // o cache do TanStack Query da sessão anterior fica visível por
        // instantes até cada query revalidar.
        queryClient.clear();
        set({ token: t, user: parseJwtPayload(t) });
      },
      clearToken: () => {
        queryClient.clear();
        set({ token: null, user: null });
      },
    }),
    {
      name: "auth",
      onRehydrateStorage: () => (state) => {
        if (state?.token) {
          state.user = parseJwtPayload(state.token);
        }
      },
    }
  )
);
