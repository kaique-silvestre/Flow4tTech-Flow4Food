import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface AppAnnouncement {
  id: number;
  title: string;
  body: string;
  expires_at: string | null;
  created_at: string | null;
}

export function useActiveAnnouncements() {
  return useQuery<AppAnnouncement[]>({
    queryKey: ["app-announcements"],
    queryFn: () => api.get<AppAnnouncement[]>("/api/app/announcements").then((r) => r.data),
    refetchInterval: 5 * 60 * 1000,
  });
}

export function useMarkAnnouncementRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.post(`/api/app/announcements/${id}/read`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["app-announcements"] });
    },
  });
}
