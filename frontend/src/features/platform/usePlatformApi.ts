import axios from "axios";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { usePlatformAuthStore } from "@/stores/platformAuthStore";

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

function authHeaders() {
  const token = usePlatformAuthStore.getState().token;
  return { Authorization: `Bearer ${token}` };
}

// ─── Types ───────────────────────────────────────────────────────────────────

export interface TenantListItem {
  id: number;
  nome_fantasia: string;
  cnpj: string | null;
  status_tenant: string;
  status_assinatura: string | null;
  data_vencimento: string | null;
  qtd_usuarios: number;
  max_users: number;
}

export interface TenantDetail {
  id: number;
  nome_fantasia: string;
  cnpj: string | null;
  endereco: string | null;
  telefone: string | null;
  max_users: number;
  status_tenant: string;
  status_assinatura: string | null;
  data_vencimento: string | null;
  qtd_usuarios: number;
}

export interface TenantUserItem {
  id: number;
  name: string;
  username: string;
  email: string | null;
  profile_id: number | null;
  profile_name: string | null;
  last_login: string | null;
  is_active: boolean;
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

export interface AnnouncementItem {
  id: number;
  title: string;
  body: string;
  expires_at: string | null;
  target: string;
  is_active: boolean;
  created_at: string | null;
  read_count: number;
}

export interface AnnouncementCreate {
  title: string;
  body: string;
  expires_at?: string | null;
  target: "all" | "specific";
  tenant_ids?: number[];
}

export interface ProfileItem {
  id: number;
  name: string;
  description: string | null;
  is_active: boolean;
  permissions: string[];
  user_count: number;
}

export interface FeatureItem {
  feature: string;
  enabled: boolean;
}

export interface AssinaturaHistoryItem {
  id: number;
  from_status: string | null;
  to_status: string;
  changed_by: number | null;
  changed_by_name: string | null;
  created_at: string;
}

export interface PlatformSettingItem {
  key: string;
  value: string;
  updated_at: string | null;
}

// ─── Tenants ─────────────────────────────────────────────────────────────────

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

export function useTenantDetail(tenantId: number | null) {
  return useQuery<TenantDetail>({
    queryKey: ["platform-tenant-detail", tenantId],
    queryFn: async () => {
      const { data } = await axios.get(`${BASE}/api/platform/tenants/${tenantId}`, {
        headers: authHeaders(),
      });
      return data;
    },
    enabled: tenantId !== null,
  });
}

export function useCreateTenant() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      nome_fantasia: string;
      cnpj?: string;
      endereco?: string;
      telefone?: string;
      max_users: number;
      trial_days?: number;
    }) => {
      const { data } = await axios.post(`${BASE}/api/platform/tenants`, body, {
        headers: authHeaders(),
      });
      return data as TenantListItem;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["platform-tenants"] });
    },
  });
}

export function useUpdateTenant() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      tenantId,
      ...body
    }: {
      tenantId: number;
      nome_fantasia?: string;
      cnpj?: string;
      endereco?: string;
      telefone?: string;
      max_users?: number;
    }) => {
      const { data } = await axios.patch(`${BASE}/api/platform/tenants/${tenantId}`, body, {
        headers: authHeaders(),
      });
      return data as TenantDetail;
    },
    onSuccess: (_data, vars) => {
      void queryClient.invalidateQueries({ queryKey: ["platform-tenant-detail", vars.tenantId] });
      void queryClient.invalidateQueries({ queryKey: ["platform-tenants"] });
    },
  });
}

// ─── Assinatura ───────────────────────────────────────────────────────────────

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

export function useUpdateAssinaturaFull() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      tenantId,
      status,
      data_vencimento,
    }: {
      tenantId: number;
      status: string;
      data_vencimento?: string | null;
    }) => {
      const { data } = await axios.patch(
        `${BASE}/api/platform/tenants/${tenantId}/assinatura/full`,
        { status, data_vencimento: data_vencimento ?? null },
        { headers: authHeaders() }
      );
      return data;
    },
    onSuccess: (_data, vars) => {
      void queryClient.invalidateQueries({ queryKey: ["platform-tenants"] });
      void queryClient.invalidateQueries({ queryKey: ["platform-tenant-detail", vars.tenantId] });
      void queryClient.invalidateQueries({ queryKey: ["platform-assinatura-history", vars.tenantId] });
    },
  });
}

export function useAssinaturaHistory(tenantId: number | null) {
  return useQuery<AssinaturaHistoryItem[]>({
    queryKey: ["platform-assinatura-history", tenantId],
    queryFn: async () => {
      const { data } = await axios.get(
        `${BASE}/api/platform/tenants/${tenantId}/assinatura/historico`,
        { headers: authHeaders() }
      );
      return data;
    },
    enabled: tenantId !== null,
  });
}

// ─── Tenant Users ─────────────────────────────────────────────────────────────

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

export function useCreateTenantUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      tenantId,
      ...body
    }: {
      tenantId: number;
      name: string;
      username: string;
      email?: string;
      password: string;
      profile_id?: number;
      is_active?: boolean;
    }) => {
      const { data } = await axios.post(
        `${BASE}/api/platform/tenants/${tenantId}/users`,
        body,
        { headers: authHeaders() }
      );
      return data as TenantUserItem;
    },
    onSuccess: (_data, vars) => {
      void queryClient.invalidateQueries({ queryKey: ["platform-tenant-users", vars.tenantId] });
      void queryClient.invalidateQueries({ queryKey: ["platform-tenant-detail", vars.tenantId] });
    },
  });
}

export function useUpdateTenantUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      tenantId,
      userId,
      ...body
    }: {
      tenantId: number;
      userId: number;
      name?: string;
      username?: string;
      email?: string;
      password?: string;
      profile_id?: number;
      is_active?: boolean;
    }) => {
      const { data } = await axios.patch(
        `${BASE}/api/platform/tenants/${tenantId}/users/${userId}`,
        body,
        { headers: authHeaders() }
      );
      return data as TenantUserItem;
    },
    onSuccess: (_data, vars) => {
      void queryClient.invalidateQueries({ queryKey: ["platform-tenant-users", vars.tenantId] });
      void queryClient.invalidateQueries({ queryKey: ["platform-tenant-detail", vars.tenantId] });
    },
  });
}

export function useImpersonateUser() {
  return useMutation({
    mutationFn: async ({ tenantId, userId }: { tenantId: number; userId: number }) => {
      const { data } = await axios.post(
        `${BASE}/api/platform/tenants/${tenantId}/users/${userId}/impersonate`,
        {},
        { headers: authHeaders() }
      );
      return data as { access_token: string };
    },
  });
}

// ─── Profiles ─────────────────────────────────────────────────────────────────

export function useTenantProfiles(tenantId: number | null) {
  return useQuery<ProfileItem[]>({
    queryKey: ["platform-tenant-profiles", tenantId],
    queryFn: async () => {
      const { data } = await axios.get(
        `${BASE}/api/platform/tenants/${tenantId}/profiles`,
        { headers: authHeaders() }
      );
      return data;
    },
    enabled: tenantId !== null,
  });
}

export function useUpdateTenantProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      tenantId,
      profileId,
      permissions,
      is_active,
    }: {
      tenantId: number;
      profileId: number;
      permissions?: string[];
      is_active?: boolean;
    }) => {
      const { data } = await axios.patch(
        `${BASE}/api/platform/tenants/${tenantId}/profiles/${profileId}`,
        { permissions, is_active },
        { headers: authHeaders() }
      );
      return data as ProfileItem;
    },
    onSuccess: (_data, vars) => {
      void queryClient.invalidateQueries({ queryKey: ["platform-tenant-profiles", vars.tenantId] });
    },
  });
}

// ─── Feature Flags ────────────────────────────────────────────────────────────

export function useTenantFeatures(tenantId: number | null) {
  return useQuery<FeatureItem[]>({
    queryKey: ["platform-tenant-features", tenantId],
    queryFn: async () => {
      const { data } = await axios.get(
        `${BASE}/api/platform/tenants/${tenantId}/features`,
        { headers: authHeaders() }
      );
      return data;
    },
    enabled: tenantId !== null,
  });
}

export function useUpsertTenantFeatures() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      tenantId,
      features,
    }: {
      tenantId: number;
      features: Record<string, boolean>;
    }) => {
      const { data } = await axios.put(
        `${BASE}/api/platform/tenants/${tenantId}/features`,
        { features },
        { headers: authHeaders() }
      );
      return data as FeatureItem[];
    },
    onSuccess: (_data, vars) => {
      void queryClient.invalidateQueries({ queryKey: ["platform-tenant-features", vars.tenantId] });
    },
  });
}

// ─── Settings ─────────────────────────────────────────────────────────────────

export function usePlatformSettings() {
  return useQuery<PlatformSettingItem[]>({
    queryKey: ["platform-settings"],
    queryFn: async () => {
      const { data } = await axios.get(`${BASE}/api/platform/settings`, {
        headers: authHeaders(),
      });
      return data;
    },
  });
}

export function useUpdateSetting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ key, value }: { key: string; value: string }) => {
      const { data } = await axios.patch(
        `${BASE}/api/platform/settings/${key}`,
        { value },
        { headers: authHeaders() }
      );
      return data as PlatformSettingItem;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["platform-settings"] });
    },
  });
}

// ─── Cockpit ──────────────────────────────────────────────────────────────────

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

// ─── Announcements ────────────────────────────────────────────────────────────

export function usePlatformAnnouncements() {
  return useQuery<AnnouncementItem[]>({
    queryKey: ["platform-announcements"],
    queryFn: async () => {
      const { data } = await axios.get(`${BASE}/api/platform/announcements`, {
        headers: authHeaders(),
      });
      return data;
    },
  });
}

export function useCreateAnnouncement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: AnnouncementCreate) => {
      const { data } = await axios.post(`${BASE}/api/platform/announcements`, body, {
        headers: authHeaders(),
      });
      return data as AnnouncementItem;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["platform-announcements"] });
    },
  });
}

// ─── Audit Logs ──────────────────────────────────────────────────────────────

export interface AuditLogItem {
  id: number;
  tenant_id: number | null;
  tenant_name: string | null;
  user_id: number | null;
  user_name: string | null;
  action: string;
  entity: string | null;
  entity_id: number | null;
  impersonated_by: number | null;
  created_at: string;
}

export interface AuditLogListResponse {
  items: AuditLogItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface AuditLogFilters {
  tenant_id?: number;
  user_id?: number;
  action?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export function useAuditLogs(filters: AuditLogFilters = {}) {
  return useQuery<AuditLogListResponse>({
    queryKey: ["platform-audit-logs", filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.tenant_id != null) params.set("tenant_id", String(filters.tenant_id));
      if (filters.user_id != null) params.set("user_id", String(filters.user_id));
      if (filters.action) params.set("action", filters.action);
      if (filters.date_from) params.set("date_from", filters.date_from);
      if (filters.date_to) params.set("date_to", filters.date_to);
      if (filters.page != null) params.set("page", String(filters.page));
      if (filters.page_size != null) params.set("page_size", String(filters.page_size));
      const { data } = await axios.get(`${BASE}/api/platform/audit-logs?${params.toString()}`, {
        headers: authHeaders(),
      });
      return data as AuditLogListResponse;
    },
  });
}
