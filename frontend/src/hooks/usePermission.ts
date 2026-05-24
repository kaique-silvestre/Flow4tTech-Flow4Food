import { useAuthStore } from "@/stores/authStore";

export function usePermission(screen: string): boolean {
  const user = useAuthStore((s) => s.user);
  if (!user) return false;
  return user.permissions.includes(screen);
}

export function usePermissions(): string[] {
  return useAuthStore((s) => s.user?.permissions ?? []);
}
