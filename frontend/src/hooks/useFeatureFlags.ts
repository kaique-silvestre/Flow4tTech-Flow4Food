import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

interface FeatureItem {
  feature: string;
  enabled: boolean;
}

export function useFeatureFlags(): Record<string, boolean> {
  const user = useAuthStore((s) => s.user);
  const { data = [] } = useQuery<FeatureItem[]>({
    queryKey: ["app-features", user?.tenant_id],
    queryFn: async () => {
      const resp = await api.get<FeatureItem[]>("/api/app/features");
      return resp.data;
    },
    enabled: !!user?.tenant_id,
    staleTime: 1000 * 60 * 5,
  });

  const map: Record<string, boolean> = {};
  for (const item of data) {
    map[item.feature] = item.enabled;
  }
  return map;
}

export function useIsFeatureEnabled(featureKey: string): boolean {
  const flags = useFeatureFlags();
  // No row = feature enabled by default
  if (!(featureKey in flags)) return true;
  return flags[featureKey];
}
