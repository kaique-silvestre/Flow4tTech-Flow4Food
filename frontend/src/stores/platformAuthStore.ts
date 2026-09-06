import { create } from "zustand";
import { persist } from "zustand/middleware";
import { decodeJwtPayload } from "@/lib/jwt";

export interface PlatformUser {
  admin_id: number;
  email: string;
  name: string;
  platform_admin: true;
}

function parsePlatformJwt(token: string): PlatformUser | null {
  const payload = decodeJwtPayload<PlatformUser>(token);
  if (!payload || !payload.platform_admin) return null;
  return payload;
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
