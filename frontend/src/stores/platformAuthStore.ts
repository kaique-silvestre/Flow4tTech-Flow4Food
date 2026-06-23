import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface PlatformUser {
  admin_id: number;
  email: string;
  name: string;
  platform_admin: true;
}

function parsePlatformJwt(token: string): PlatformUser | null {
  try {
    const base64 = token.split(".")[1];
    const json = atob(base64.replace(/-/g, "+").replace(/_/g, "/"));
    const payload = JSON.parse(json) as PlatformUser;
    if (!payload.platform_admin) return null;
    return payload;
  } catch {
    return null;
  }
}

interface PlatformAuthState {
  token: string | null;
  user: PlatformUser | null;
  setToken: (t: string) => void;
  clearToken: () => void;
}

export const usePlatformAuthStore = create<PlatformAuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setToken: (t) => set({ token: t, user: parsePlatformJwt(t) }),
      clearToken: () => set({ token: null, user: null }),
    }),
    {
      name: "platform-auth",
      onRehydrateStorage: () => (state) => {
        if (state?.token) {
          state.user = parsePlatformJwt(state.token);
        }
      },
    }
  )
);
