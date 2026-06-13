import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { toast } from "@/lib/toast";
import {
  useTenantDetail,
  useUpdateTenant,
  useUpdateAssinaturaFull,
  useAssinaturaHistory,
  useTenantUsers,
  useCreateTenantUser,
  useUpdateTenantUser,
  useImpersonateUser,
  useTenantProfiles,
  useUpdateTenantProfile,
  useTenantFeatures,
  useUpsertTenantFeatures,
  type TenantUserItem,
  type ProfileItem,
} from "./usePlatformApi";
import { useAuthStore } from "@/stores/authStore";

const STATUS_OPTIONS = ["trial", "ativa", "suspensa", "cancelada"] as const;
const STATUS_LABELS: Record<string, string> = { trial: "Trial", ativa: "Ativa", suspensa: "Suspensa", cancelada: "Cancelada" };
const STATUS_COLORS: Record<string, string> = {
  trial: "bg-yellow-100 text-yellow-800",
  ativa: "bg-green-100 text-green-800",
  suspensa: "bg-red-100 text-red-800",
  cancelada: "bg-gray-100 text-gray-600",
};

const AVAILABLE_FEATURES = ["compras", "relatorios", "financeiro", "cockpit", "exportar_pdf"] as const;

type Tab = "dados" | "usuarios" | "perfis" | "features";

// ─── Sub-components ───────────────────────────────────────────────────────────

function DadosTab({ tenantId }: { tenantId: number }) {
  const { data: detail, isLoading } = useTenantDetail(tenantId);
  const { data: history = [] } = useAssinaturaHistory(tenantId);
  const updateTenant = useUpdateTenant();
  const updateAssinatura = useUpdateAssinaturaFull();
  const [editing, setEditing] = useState(false);
  const [nomeFantasia, setNomeFantasia] = useState("");
  const [maxUsers, setMaxUsers] = useState(0);
  const [status, setStatus] = useState("");
  const [dataVencimento, setDataVencimento] = useState("");

  if (isLoading || !detail) return <p className="text-sm text-gray-500">Carregando…</p>;

  function startEdit() {
    setNomeFantasia(detail!.nome_fantasia);
    setMaxUsers(detail!.max_users);
    setStatus(detail!.status_assinatura ?? "");
    setDataVencimento(detail!.data_vencimento ? detail!.data_vencimento.slice(0, 16) : "");
    setEditing(true);
  }

  function handleSave() {
    updateTenant.mutate(
      { tenantId, nome_fantasia: nomeFantasia, max_users: maxUsers },
      {
        onSuccess: () => {
          if (status !== detail!.status_assinatura || dataVencimento) {
            updateAssinatura.mutate(
              { tenantId, status, data_vencimento: dataVencimento || null },
              { onSuccess: () => { toast.success("Salvo"); setEditing(false); }, onError: () => toast.error("Erro ao salvar assinatura") }
            );
          } else {
            toast.success("Salvo");
            setEditing(false);
          }
        },
        onError: () => toast.error("Erro ao salvar"),
      }
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium text-gray-900">Dados da Empresa</h3>
          {!editing && (
            <button onClick={startEdit} className="text-sm text-blue-600 hover:underline">Editar</button>
          )}
        </div>
        {editing ? (
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700">Nome Fantasia</label>
              <input
                className="mt-1 w-full rounded-lg border px-3 py-2 text-sm"
                value={nomeFantasia}
                onChange={(e) => setNomeFantasia(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Máx. Usuários</label>
              <input
                type="number"
                className="mt-1 w-full rounded-lg border px-3 py-2 text-sm"
                value={maxUsers}
                onChange={(e) => setMaxUsers(parseInt(e.target.value, 10))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Status Assinatura</label>
              <select
                className="mt-1 w-full rounded-lg border px-3 py-2 text-sm"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                {STATUS_OPTIONS.map((s) => (
                  <option key={s} value={s}>{STATUS_LABELS[s]}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Vencimento</label>
              <input
                type="datetime-local"
                className="mt-1 w-full rounded-lg border px-3 py-2 text-sm"
                value={dataVencimento}
                onChange={(e) => setDataVencimento(e.target.value)}
              />
            </div>
            <div className="flex gap-3 pt-2">
              <button
                onClick={handleSave}
                disabled={updateTenant.isPending || updateAssinatura.isPending}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
              >
                Salvar
              </button>
              <button onClick={() => setEditing(false)} className="rounded-lg border px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                Cancelar
              </button>
            </div>
          </div>
        ) : (
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-gray-500">Nome Fantasia</dt>
              <dd className="font-medium text-gray-900">{detail.nome_fantasia}</dd>
            </div>
            <div>
              <dt className="text-gray-500">CNPJ</dt>
              <dd className="font-medium text-gray-900">{detail.cnpj ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Usuários</dt>
              <dd className="font-medium text-gray-900">{detail.qtd_usuarios}/{detail.max_users}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Status Assinatura</dt>
              <dd>
                {detail.status_assinatura ? (
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[detail.status_assinatura] ?? ""}`}>
                    {STATUS_LABELS[detail.status_assinatura] ?? detail.status_assinatura}
                  </span>
                ) : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-gray-500">Vencimento</dt>
              <dd className="font-medium text-gray-900">
                {detail.data_vencimento ? new Date(detail.data_vencimento).toLocaleString("pt-BR") : "—"}
              </dd>
            </div>
          </dl>
        )}
      </div>

      {history.length > 0 && (
        <div className="bg-white rounded-xl border p-5">
          <h3 className="font-medium text-gray-900 mb-3">Histórico de Assinatura</h3>
          <div className="space-y-2">
            {history.map((h) => (
              <div key={h.id} className="flex items-center gap-3 text-sm text-gray-700">
                <span className="text-gray-400 text-xs">{new Date(h.created_at).toLocaleString("pt-BR")}</span>
                <span className="text-gray-400">→</span>
                <span>{h.from_status ?? "—"}</span>
                <span className="text-gray-400">→</span>
                <span className="font-medium">{h.to_status}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function UsuariosTab({ tenantId }: { tenantId: number }) {
  const { data: users = [], isLoading } = useTenantUsers(tenantId);
  const createUser = useCreateTenantUser();
  const updateUser = useUpdateTenantUser();
  const impersonate = useImpersonateUser();
  const setToken = useAuthStore((s) => s.setToken);
  const [addOpen, setAddOpen] = useState(false);
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    createUser.mutate(
      { tenantId, name: name.trim(), username: username.trim(), email: email.trim() || undefined, password },
      {
        onSuccess: () => { toast.success("Usuário criado"); setAddOpen(false); setName(""); setUsername(""); setEmail(""); setPassword(""); },
        onError: () => toast.error("Erro ao criar usuário"),
      }
    );
  }

  function handleToggleActive(u: TenantUserItem) {
    updateUser.mutate(
      { tenantId, userId: u.id, is_active: !u.is_active },
      { onSuccess: () => toast.success("Atualizado"), onError: () => toast.error("Erro") }
    );
  }

  function handleImpersonate(u: TenantUserItem) {
    impersonate.mutate(
      { tenantId, userId: u.id },
      {
        onSuccess: ({ access_token }) => {
          setToken(access_token);
          window.open("/", "_blank");
          toast.success(`Impersonando ${u.name}`);
        },
        onError: () => toast.error("Erro ao impersonar"),
      }
    );
  }

  if (isLoading) return <p className="text-sm text-gray-500">Carregando…</p>;

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button
          onClick={() => setAddOpen(true)}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
        >
          + Novo Usuário
        </button>
      </div>

      {addOpen && (
        <div className="bg-white rounded-xl border p-4">
          <form onSubmit={handleCreate} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700">Nome</label>
                <input className="mt-1 w-full rounded-lg border px-3 py-2 text-sm" value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Username</label>
                <input className="mt-1 w-full rounded-lg border px-3 py-2 text-sm" value={username} onChange={(e) => setUsername(e.target.value)} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Email</label>
                <input type="email" className="mt-1 w-full rounded-lg border px-3 py-2 text-sm" value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Senha</label>
                <input type="password" className="mt-1 w-full rounded-lg border px-3 py-2 text-sm" value={password} onChange={(e) => setPassword(e.target.value)} />
              </div>
            </div>
            <div className="flex gap-3">
              <button type="submit" disabled={createUser.isPending} className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50">
                {createUser.isPending ? "Criando..." : "Criar"}
              </button>
              <button type="button" onClick={() => setAddOpen(false)} className="rounded-lg border px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-left">
            <tr>
              <th className="px-4 py-3 font-medium">Nome</th>
              <th className="px-4 py-3 font-medium">Username</th>
              <th className="px-4 py-3 font-medium">Perfil</th>
              <th className="px-4 py-3 font-medium">Último Login</th>
              <th className="px-4 py-3 font-medium">Ativo</th>
              <th className="px-4 py-3 font-medium">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{u.name}</td>
                <td className="px-4 py-3 text-gray-500">{u.username}</td>
                <td className="px-4 py-3">{u.profile_name ?? "—"}</td>
                <td className="px-4 py-3 text-gray-500">{u.last_login ? new Date(u.last_login).toLocaleString("pt-BR") : "Nunca"}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${u.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                    {u.is_active ? "Sim" : "Não"}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleToggleActive(u)}
                      className={`text-xs px-2 py-1 rounded ${u.is_active ? "bg-gray-100 text-gray-700 hover:bg-gray-200" : "bg-green-100 text-green-700 hover:bg-green-200"}`}
                    >
                      {u.is_active ? "Desativar" : "Ativar"}
                    </button>
                    <button
                      onClick={() => handleImpersonate(u)}
                      className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-700 hover:bg-blue-200"
                    >
                      Impersonar
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">Nenhum usuário</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function PerfisTab({ tenantId }: { tenantId: number }) {
  const { data: profiles = [], isLoading } = useTenantProfiles(tenantId);
  const updateProfile = useUpdateTenantProfile();
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editPerms, setEditPerms] = useState<string[]>([]);

  const ALL_SCREENS = ["dashboard", "caixa", "cardapio", "compras", "estoque", "financeiro", "relatorios", "cadastros", "configuracoes"];

  function startEdit(p: ProfileItem) {
    setEditingId(p.id);
    setEditPerms([...p.permissions]);
  }

  function togglePerm(screen: string) {
    setEditPerms((prev) => prev.includes(screen) ? prev.filter((s) => s !== screen) : [...prev, screen]);
  }

  function handleSave(p: ProfileItem) {
    updateProfile.mutate(
      { tenantId, profileId: p.id, permissions: editPerms },
      {
        onSuccess: () => { toast.success("Perfil atualizado"); setEditingId(null); },
        onError: () => toast.error("Erro ao salvar"),
      }
    );
  }

  if (isLoading) return <p className="text-sm text-gray-500">Carregando…</p>;

  return (
    <div className="space-y-3">
      {profiles.map((p) => (
        <div key={p.id} className="bg-white rounded-xl border p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="font-medium text-gray-900">{p.name}</span>
            {editingId !== p.id ? (
              <button onClick={() => startEdit(p)} className="text-sm text-blue-600 hover:underline">Editar permissões</button>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={() => handleSave(p)}
                  disabled={updateProfile.isPending}
                  className="text-sm px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  Salvar
                </button>
                <button onClick={() => setEditingId(null)} className="text-sm px-3 py-1 border text-gray-700 rounded hover:bg-gray-50">
                  Cancelar
                </button>
              </div>
            )}
          </div>
          {editingId === p.id ? (
            <div className="flex flex-wrap gap-2">
              {ALL_SCREENS.map((screen) => (
                <label key={screen} className="flex items-center gap-1.5 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editPerms.includes(screen)}
                    onChange={() => togglePerm(screen)}
                  />
                  {screen}
                </label>
              ))}
            </div>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {p.permissions.length > 0 ? p.permissions.map((perm) => (
                <span key={perm} className="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-700">{perm}</span>
              )) : <span className="text-xs text-gray-400">Nenhuma permissão</span>}
            </div>
          )}
        </div>
      ))}
      {profiles.length === 0 && <p className="text-sm text-gray-400">Nenhum perfil cadastrado</p>}
    </div>
  );
}

function FeaturesTab({ tenantId }: { tenantId: number }) {
  const { data: features = [], isLoading } = useTenantFeatures(tenantId);
  const upsert = useUpsertTenantFeatures();
  const [localFeatures, setLocalFeatures] = useState<Record<string, boolean>>({});
  const [initialized, setInitialized] = useState(false);

  if (!initialized && features.length > 0) {
    const map: Record<string, boolean> = {};
    for (const f of features) map[f.feature] = f.enabled;
    for (const f of AVAILABLE_FEATURES) if (!(f in map)) map[f] = false;
    setLocalFeatures(map);
    setInitialized(true);
  }

  if (!initialized && features.length === 0 && !isLoading) {
    const map: Record<string, boolean> = {};
    for (const f of AVAILABLE_FEATURES) map[f] = false;
    setLocalFeatures(map);
    setInitialized(true);
  }

  function toggleFeature(key: string) {
    setLocalFeatures((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  function handleSave() {
    upsert.mutate(
      { tenantId, features: localFeatures },
      { onSuccess: () => toast.success("Feature flags atualizadas"), onError: () => toast.error("Erro ao salvar") }
    );
  }

  if (isLoading) return <p className="text-sm text-gray-500">Carregando…</p>;

  return (
    <div className="bg-white rounded-xl border p-5 space-y-4">
      <h3 className="font-medium text-gray-900">Feature Flags</h3>
      <div className="space-y-3">
        {AVAILABLE_FEATURES.map((feature) => (
          <label key={feature} className="flex items-center gap-3 cursor-pointer">
            <div
              className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${localFeatures[feature] ? "bg-blue-600" : "bg-gray-200"}`}
              onClick={() => toggleFeature(feature)}
            >
              <span className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition-transform ${localFeatures[feature] ? "translate-x-4" : "translate-x-0"}`} />
            </div>
            <span className="text-sm text-gray-700 capitalize">{feature.replace(/_/g, " ")}</span>
          </label>
        ))}
      </div>
      <button
        onClick={handleSave}
        disabled={upsert.isPending}
        className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {upsert.isPending ? "Salvando..." : "Salvar"}
      </button>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

const TABS: { key: Tab; label: string }[] = [
  { key: "dados", label: "Dados & Assinatura" },
  { key: "usuarios", label: "Usuários" },
  { key: "perfis", label: "Perfis" },
  { key: "features", label: "Feature Flags" },
];

export function PlatformTenantDetailPage() {
  const { tenantId } = useParams<{ tenantId: string }>();
  const id = tenantId ? parseInt(tenantId, 10) : null;
  const { data: detail } = useTenantDetail(id);
  const [activeTab, setActiveTab] = useState<Tab>("dados");

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Link to="/platform/tenants" className="text-sm text-blue-600 hover:underline">
          ← Empresas
        </Link>
        <h1 className="text-xl font-semibold text-gray-900">
          {detail?.nome_fantasia ?? `Empresa #${tenantId}`}
        </h1>
        {detail?.status_assinatura && (
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[detail.status_assinatura] ?? ""}`}>
            {STATUS_LABELS[detail.status_assinatura] ?? detail.status_assinatura}
          </span>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-0">
          {TABS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                activeTab === key
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      {id !== null && (
        <>
          {activeTab === "dados" && <DadosTab tenantId={id} />}
          {activeTab === "usuarios" && <UsuariosTab tenantId={id} />}
          {activeTab === "perfis" && <PerfisTab tenantId={id} />}
          {activeTab === "features" && <FeaturesTab tenantId={id} />}
        </>
      )}
    </div>
  );
}
