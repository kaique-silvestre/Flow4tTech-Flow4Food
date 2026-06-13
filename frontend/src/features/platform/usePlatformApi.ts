import axios from "axios";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { usePlatformAuthStore } from "@/stores/platformAuthStore";

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

function authHeaders() {
  const token = usePlatformAuthStore.getState().token;
  return { Authorization: `Bearer ${token}` };
}

export interface TenantListItem {
  id: number;
  nome_fantasia: string;
  cnpj: string | null;
  status_tenant: string;
  status_assinatura: string | null;
  data_vencimento: string | null;
}

export interface TenantUserItem {
  id: number;
  name: string;
  username: string;
  profile_name: string;
  last_login: string | null;
  is_active: boolean;
}

export function useTenants(statusFilter?: string) {
  return useQuery<TenantListItem[]>({
    queryKey: ["platform-tenants", statusFilter],
    queryFn: async () => {
      const params = statusFilter ? { status: statusFilter } : {};
      const { data } = await axios.get(`${BASE}/api/platform/tenants`, {
        headers: authHeaders(),
        params,
      });
      return data;
    },
  });
}

export function useTenantUsers(tenantId: number | null) {
  return useQuery<TenantUserItem[]>({
    queryKey: ["platform-tenant-users", tenantId],
    queryFn: async () => {
      const { data } = await axios.get(`${BASE}/api/platform/tenants/${tenantId}/users`, {
        headers: authHeaders(),
      });
      return data;
    },
    enabled: tenantId !== null,
  });
}

export interface CockpitMetricsItem {
  id: number;
  nome_fantasia: string;
  cnpj: string | null;
  status_tenant: string;
  status_assinatura: string | null;
  dias_cliente: number;
  ultimo_login: string | null;
  comandas_mes: number;
  faturamento_mes: number;
  usuarios_ativos_30d: number;
  compras_mes: number;
}

export function usePlatformCockpit(statusFilter?: string) {
  return useQuery<CockpitMetricsItem[]>({
    queryKey: ["platform-cockpit", statusFilter],
    queryFn: async () => {
      const params = statusFilter ? { status: statusFilter } : {};
      const { data } = await axios.get(`${BASE}/api/platform/cockpit`, {
        headers: authHeaders(),
        params,
      });
      return data;
    },
  });
}

export function useTenantCockpit(tenantId: number | null) {
  return useQuery<CockpitMetricsItem>({
    queryKey: ["platform-tenant-cockpit", tenantId],
    queryFn: async () => {
      const { data } = await axios.get(
        `${BASE}/api/platform/tenants/${tenantId}/cockpit`,
        { headers: authHeaders() }
      );
      return data;
    },
    enabled: tenantId !== null,
  });
}

export function useUpdateAssinatura() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ tenantId, status }: { tenantId: number; status: string }) => {
      const { data } = await axios.patch(
        `${BASE}/api/platform/tenants/${tenantId}/assinatura`,
        { status },
        { headers: authHeaders() }
      );
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["platform-tenants"] });
    },
  });
}
