import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface AuthUser {
  user_id: number;
  tenant_id: number;
  username: string;
  name: string;
  profile_id: number;
  profile_name: string;
  permissions: string[];
  subscription_status?: string;
}

function parseJwtPayload(token: string): AuthUser | null {
  try {
    const base64 = token.split(".")[1];
    const json = atob(base64.replace(/-/g, "+").replace(/_/g, "/"));
    const payload = JSON.parse(json) as AuthUser;
    if (!Array.isArray(payload.permissions)) return null;
    return payload;
  } catch {
    return null;
  }
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
      setToken: (t) => set({ token: t, user: parseJwtPayload(t) }),
      clearToken: () => set({ token: null, user: null }),
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
