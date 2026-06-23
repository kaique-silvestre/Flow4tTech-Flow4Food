import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { toast } from "@/lib/toast";

export interface PermissionTemplate {
  id: number;
  tenant_id: number | null;
  nome: string;
  descricao: string | null;
  is_system: boolean;
  screens: string[];
}

function errMsg(e: unknown, fallback: string): string {
  if (e && typeof e === "object" && "response" in e) {
    const r = (e as { response?: { data?: { error?: { message?: string } } } }).response;
    return r?.data?.error?.message ?? fallback;
  }
  return fallback;
}

export function usePermissionTemplates() {
  return useQuery({
    queryKey: ["permission-templates"],
    queryFn: () =>
      api.get<PermissionTemplate[]>("/api/permission-templates").then((r) => r.data),
  });
}

export function useAssignProfileTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ profileId, templateId }: { profileId: number; templateId: number | null }) =>
      api.patch(`/api/profiles/${profileId}/template`, { template_id: templateId }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["profiles"] });
    },
    onError: (e: unknown) => toast.error(errMsg(e, "Erro ao aplicar template")),
  });
}
