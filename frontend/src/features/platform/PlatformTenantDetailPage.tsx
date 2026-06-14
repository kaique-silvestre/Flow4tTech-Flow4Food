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
import { IMPERSONATION_SESSION_KEY } from "@/App";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";

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
  const [cnpj, setCnpj] = useState("");
  const [endereco, setEndereco] = useState("");
  const [telefone, setTelefone] = useState("");
  const [maxUsers, setMaxUsers] = useState(0);
  const [status, setStatus] = useState("");
  const [dataVencimento, setDataVencimento] = useState("");

  if (isLoading || !detail) return <p className="text-sm text-gray-500">Carregando…</p>;

  function startEdit() {
    setNomeFantasia(detail!.nome_fantasia);
    setCnpj(detail!.cnpj ?? "");
    setEndereco(detail!.endereco ?? "");
    setTelefone(detail!.telefone ?? "");
    setMaxUsers(detail!.max_users);
    setStatus(detail!.status_assinatura ?? "");
    setDataVencimento(detail!.data_vencimento ? detail!.data_vencimento.slice(0, 16) : "");
    setEditing(true);
  }

  function handleSave() {
    updateTenant.mutate(
      { tenantId, nome_fantasia: nomeFantasia, cnpj: cnpj || undefined, endereco: endereco || undefined, telefone: telefone || undefined, max_users: maxUsers },
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
              <label className="block text-sm font-medium text-gray-700">CNPJ</label>
              <input
                className="mt-1 w-full rounded-lg border px-3 py-2 text-sm"
                placeholder="00.000.000/0000-00"
                value={cnpj}
                onChange={(e) => setCnpj(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Endereço</label>
              <input
                className="mt-1 w-full rounded-lg border px-3 py-2 text-sm"
                value={endereco}
                onChange={(e) => setEndereco(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Telefone</label>
              <input
                className="mt-1 w-full rounded-lg border px-3 py-2 text-sm"
                value={telefone}
                onChange={(e) => setTelefone(e.target.value)}
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
            <div className="col-span-2">
              <dt className="text-gray-500">Endereço</dt>
              <dd className="font-medium text-gray-900">{detail.endereco ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Telefone</dt>
              <dd className="font-medium text-gray-900">{detail.telefone ?? "—"}</dd>
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
                <span className="text-gray-400">·</span>
                <span>{h.from_status ?? "—"}</span>
                <span className="text-gray-400">→</span>
                <span className="font-medium">{h.to_status}</span>
                {h.changed_by_name && (
                  <>
                    <span className="text-gray-400">·</span>
                    <span className="text-gray-500 text-xs">{h.changed_by_name}</span>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

type UserFormState = {
  name: string;
  username: string;
  email: string;
  password: string;
  profile_id: string;
  is_active: boolean;
};

const EMPTY_FORM: UserFormState = { name: "", username: "", email: "", password: "", profile_id: "", is_active: true };

function UsuariosTab({ tenantId }: { tenantId: number }) {
  const { data: detail } = useTenantDetail(tenantId);
  const { data: users = [], isLoading } = useTenantUsers(tenantId);
  const { data: profiles = [] } = useTenantProfiles(tenantId);
  const createUser = useCreateTenantUser();
  const updateUser = useUpdateTenantUser();
  const updateTenant = useUpdateTenant();
  const impersonate = useImpersonateUser();

  const [modalMode, setModalMode] = useState<"create" | "edit" | null>(null);
  const [editTarget, setEditTarget] = useState<TenantUserItem | null>(null);
  const [form, setForm] = useState<UserFormState>(EMPTY_FORM);
  const [confirmToggle, setConfirmToggle] = useState<TenantUserItem | null>(null);
  const [editingMaxUsers, setEditingMaxUsers] = useState(false);
  const [maxUsersVal, setMaxUsersVal] = useState(0);

  const activeCount = users.filter((u) => u.is_active).length;

  function openCreate() {
    setForm(EMPTY_FORM);
    setEditTarget(null);
    setModalMode("create");
  }

  function openEdit(u: TenantUserItem) {
    setForm({
      name: u.name,
      username: u.username,
      email: u.email ?? "",
      password: "",
      profile_id: u.profile_id != null ? String(u.profile_id) : "",
      is_active: u.is_active,
    });
    setEditTarget(u);
    setModalMode("edit");
  }

  function closeModal() {
    setModalMode(null);
    setEditTarget(null);
    setForm(EMPTY_FORM);
  }

  function setField<K extends keyof UserFormState>(k: K, v: UserFormState[K]) {
    setForm((prev) => ({ ...prev, [k]: v }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const profileId = form.profile_id ? parseInt(form.profile_id, 10) : undefined;

    if (modalMode === "create") {
      createUser.mutate(
        {
          tenantId,
          name: form.name.trim(),
          username: form.username.trim(),
          email: form.email.trim() || undefined,
          password: form.password,
          profile_id: profileId,
          is_active: form.is_active,
        },
        { onSuccess: () => { toast.success("Usuário criado"); closeModal(); }, onError: () => toast.error("Erro ao criar usuário") }
      );
    } else if (modalMode === "edit" && editTarget) {
      updateUser.mutate(
        {
          tenantId,
          userId: editTarget.id,
          name: form.name.trim(),
          username: form.username.trim(),
          email: form.email.trim() || undefined,
          password: form.password || undefined,
          profile_id: profileId,
          is_active: form.is_active,
        },
        { onSuccess: () => { toast.success("Usuário atualizado"); closeModal(); }, onError: () => toast.error("Erro ao atualizar") }
      );
    }
  }

  function confirmToggleActive() {
    if (!confirmToggle) return;
    updateUser.mutate(
      { tenantId, userId: confirmToggle.id, is_active: !confirmToggle.is_active },
      {
        onSuccess: () => { toast.success("Atualizado"); setConfirmToggle(null); },
        onError: () => { toast.error("Erro"); setConfirmToggle(null); },
      }
    );
  }

  function handleImpersonate(u: TenantUserItem) {
    impersonate.mutate(
      { tenantId, userId: u.id },
      {
        onSuccess: ({ access_token }) => {
          sessionStorage.setItem(IMPERSONATION_SESSION_KEY, access_token);
          window.open(`/?impersonation_token=${access_token}`, "_blank");
          toast.success(`Sessão de suporte iniciada como ${u.name}`);
        },
        onError: () => toast.error("Erro ao iniciar sessão de suporte"),
      }
    );
  }

  function startEditMaxUsers() {
    setMaxUsersVal(detail?.max_users ?? 0);
    setEditingMaxUsers(true);
  }

  function saveMaxUsers() {
    updateTenant.mutate(
      { tenantId, max_users: maxUsersVal },
      {
        onSuccess: () => { toast.success("Limite atualizado"); setEditingMaxUsers(false); },
        onError: () => toast.error("Erro ao atualizar limite"),
      }
    );
  }

  if (isLoading) return <p className="text-sm text-gray-500">Carregando…</p>;

  const isPending = createUser.isPending || updateUser.isPending;

  return (
    <div className="space-y-4">
      {/* Indicator + max_users edit */}
      <div className="flex items-center justify-between bg-white rounded-xl border px-5 py-3">
        <span className="text-sm text-gray-700">
          <span className="font-semibold text-gray-900">{activeCount}</span>
          {" / "}
          {editingMaxUsers ? (
            <span className="inline-flex items-center gap-2">
              <input
                type="number"
                min={1}
                className="w-16 rounded border px-2 py-0.5 text-sm"
                value={maxUsersVal}
                onChange={(e) => setMaxUsersVal(parseInt(e.target.value, 10) || 1)}
              />
              <button onClick={saveMaxUsers} disabled={updateTenant.isPending} className="text-xs px-2 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50">
                OK
              </button>
              <button onClick={() => setEditingMaxUsers(false)} className="text-xs px-2 py-1 rounded border text-gray-600 hover:bg-gray-50">
                ✕
              </button>
            </span>
          ) : (
            <span>
              <span className="font-semibold text-gray-900">{detail?.max_users ?? "…"}</span>
              {" "}
              <button onClick={startEditMaxUsers} className="text-xs text-blue-600 hover:underline ml-1">editar</button>
            </span>
          )}
          {" "}usuários ativos
        </span>
        <button
          onClick={openCreate}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
        >
          + Novo Usuário
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-left">
            <tr>
              <th className="px-4 py-3 font-medium">Nome</th>
              <th className="px-4 py-3 font-medium">Username</th>
              <th className="px-4 py-3 font-medium">E-mail</th>
              <th className="px-4 py-3 font-medium">Perfil</th>
              <th className="px-4 py-3 font-medium">Último Login</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{u.name}</td>
                <td className="px-4 py-3 text-gray-500">{u.username}</td>
                <td className="px-4 py-3 text-gray-500">{u.email ?? "—"}</td>
                <td className="px-4 py-3">{u.profile_name ?? "—"}</td>
                <td className="px-4 py-3 text-gray-500">{u.last_login ? new Date(u.last_login).toLocaleString("pt-BR") : "Nunca"}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${u.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                    {u.is_active ? "Ativo" : "Inativo"}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <button
                      onClick={() => openEdit(u)}
                      className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700 hover:bg-gray-200"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => setConfirmToggle(u)}
                      className={`text-xs px-2 py-1 rounded ${u.is_active ? "bg-orange-100 text-orange-700 hover:bg-orange-200" : "bg-green-100 text-green-700 hover:bg-green-200"}`}
                    >
                      {u.is_active ? "Desativar" : "Ativar"}
                    </button>
                    <button
                      onClick={() => handleImpersonate(u)}
                      className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-700 hover:bg-blue-200"
                    >
                      Entrar como
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-400">Nenhum usuário</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Create / Edit modal */}
      {modalMode !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <h2 className="text-base font-semibold text-gray-900 mb-4">
              {modalMode === "create" ? "Novo Usuário" : "Editar Usuário"}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Nome</label>
                  <input required className="mt-1 w-full rounded-lg border px-3 py-2 text-sm" value={form.name} onChange={(e) => setField("name", e.target.value)} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Username</label>
                  <input required className="mt-1 w-full rounded-lg border px-3 py-2 text-sm" value={form.username} onChange={(e) => setField("username", e.target.value)} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">E-mail</label>
                  <input type="email" className="mt-1 w-full rounded-lg border px-3 py-2 text-sm" value={form.email} onChange={(e) => setField("email", e.target.value)} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Senha{modalMode === "edit" && <span className="text-gray-400 font-normal"> (deixe vazio para manter)</span>}
                  </label>
                  <input
                    type="password"
                    required={modalMode === "create"}
                    className="mt-1 w-full rounded-lg border px-3 py-2 text-sm"
                    value={form.password}
                    onChange={(e) => setField("password", e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Perfil</label>
                  <select className="mt-1 w-full rounded-lg border px-3 py-2 text-sm" value={form.profile_id} onChange={(e) => setField("profile_id", e.target.value)}>
                    <option value="">— Nenhum —</option>
                    {profiles.map((p: ProfileItem) => (
                      <option key={p.id} value={String(p.id)}>{p.name}</option>
                    ))}
                  </select>
                </div>
                <div className="flex items-center gap-2 pt-5">
                  <input
                    id="is_active"
                    type="checkbox"
                    checked={form.is_active}
                    onChange={(e) => setField("is_active", e.target.checked)}
                    className="h-4 w-4 rounded border-gray-300"
                  />
                  <label htmlFor="is_active" className="text-sm font-medium text-gray-700">Ativo</label>
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="submit" disabled={isPending} className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50">
                  {isPending ? "Salvando..." : modalMode === "create" ? "Criar" : "Salvar"}
                </button>
                <button type="button" onClick={closeModal} className="rounded-lg border px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Toggle active confirmation */}
      <ConfirmDialog
        open={confirmToggle !== null}
        title={confirmToggle?.is_active ? `Desativar ${confirmToggle?.name}?` : `Ativar ${confirmToggle?.name}?`}
        description={confirmToggle?.is_active ? "O usuário perderá acesso ao sistema." : "O usuário voltará a ter acesso ao sistema."}
        confirmLabel={confirmToggle?.is_active ? "Desativar" : "Ativar"}
        isPending={updateUser.isPending}
        onConfirm={confirmToggleActive}
        onCancel={() => setConfirmToggle(null)}
      />
    </div>
  );
}

const PROFILE_SCREENS: { id: string; label: string }[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "comandas", label: "Comandas / Cardápio" },
  { id: "compras", label: "Compras" },
  { id: "estoque", label: "Estoque" },
  { id: "cadastros", label: "Cadastros" },
  { id: "relatorios", label: "Relatórios" },
  { id: "configuracoes", label: "Configurações" },
  { id: "gestao_usuarios", label: "Gestão de Usuários" },
];
const SCREEN_LABELS = Object.fromEntries(PROFILE_SCREENS.map((s) => [s.id, s.label]));

function PerfisTab({ tenantId }: { tenantId: number }) {
  const { data: profiles = [], isLoading } = useTenantProfiles(tenantId);
  const updateProfile = useUpdateTenantProfile();
  const [editingProfile, setEditingProfile] = useState<ProfileItem | null>(null);
  const [editPerms, setEditPerms] = useState<string[]>([]);
  const [confirmToggleProfile, setConfirmToggleProfile] = useState<ProfileItem | null>(null);

  function startEdit(p: ProfileItem) {
    setEditingProfile(p);
    setEditPerms([...p.permissions]);
  }

  function togglePerm(screen: string) {
    setEditPerms((prev) => prev.includes(screen) ? prev.filter((s) => s !== screen) : [...prev, screen]);
  }

  function handleSavePerms() {
    if (!editingProfile) return;
    updateProfile.mutate(
      { tenantId, profileId: editingProfile.id, permissions: editPerms },
      {
        onSuccess: () => { toast.success("Permissões atualizadas"); setEditingProfile(null); },
        onError: () => toast.error("Erro ao salvar"),
      }
    );
  }

  function handleToggleActive(p: ProfileItem) {
    if (p.is_active && p.user_count > 0) {
      setConfirmToggleProfile(p);
      return;
    }
    doToggleProfile(p);
  }

  function doToggleProfile(p: ProfileItem) {
    updateProfile.mutate(
      { tenantId, profileId: p.id, is_active: !p.is_active },
      {
        onSuccess: () => { toast.success(p.is_active ? "Perfil desativado" : "Perfil ativado"); setConfirmToggleProfile(null); },
        onError: () => toast.error("Erro ao atualizar"),
      }
    );
  }

  if (isLoading) return <p className="text-sm text-gray-500">Carregando…</p>;

  return (
    <div className="space-y-4">
      {confirmToggleProfile && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
          <p className="flex-1 text-sm font-medium text-amber-900">
            Perfil &ldquo;{confirmToggleProfile.name}&rdquo; tem {confirmToggleProfile.user_count} usuário{confirmToggleProfile.user_count !== 1 ? "s" : ""} vinculado{confirmToggleProfile.user_count !== 1 ? "s" : ""}. Confirmar desativação?
          </p>
          <div className="flex gap-2 shrink-0">
            <button
              onClick={() => doToggleProfile(confirmToggleProfile)}
              disabled={updateProfile.isPending}
              className="text-xs px-3 py-1.5 bg-amber-600 text-white rounded hover:bg-amber-700 disabled:opacity-50"
            >
              Confirmar
            </button>
            <button
              onClick={() => setConfirmToggleProfile(null)}
              className="text-xs px-3 py-1.5 border text-gray-700 rounded hover:bg-gray-50"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-left">
            <tr>
              <th className="px-4 py-3 font-medium">Nome</th>
              <th className="px-4 py-3 font-medium">Descrição</th>
              <th className="px-4 py-3 font-medium">Permissões</th>
              <th className="px-4 py-3 font-medium">Usuários</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {profiles.map((p) => (
              <tr key={p.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{p.name}</td>
                <td className="px-4 py-3 text-gray-500 max-w-[160px] truncate">{p.description ?? "—"}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {p.permissions.length > 0
                      ? p.permissions.map((perm) => (
                          <span key={perm} className="px-2 py-0.5 rounded-full text-xs bg-blue-50 text-blue-700">
                            {SCREEN_LABELS[perm] ?? perm}
                          </span>
                        ))
                      : <span className="text-xs text-gray-400">Nenhuma</span>}
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-700">{p.user_count}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${p.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                    {p.is_active ? "Ativo" : "Inativo"}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <button
                      onClick={() => startEdit(p)}
                      className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-700 hover:bg-blue-200"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => handleToggleActive(p)}
                      disabled={updateProfile.isPending}
                      className={`text-xs px-2 py-1 rounded disabled:opacity-50 ${p.is_active ? "bg-gray-100 text-gray-700 hover:bg-gray-200" : "bg-green-100 text-green-700 hover:bg-green-200"}`}
                    >
                      {p.is_active ? "Desativar" : "Ativar"}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {profiles.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">Nenhum perfil cadastrado</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {editingProfile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <h3 className="text-base font-semibold text-gray-900 mb-1">Editar permissões</h3>
            <p className="text-sm text-gray-500 mb-4">{editingProfile.name}</p>
            <div className="space-y-2.5 mb-6">
              {PROFILE_SCREENS.map((screen) => (
                <label key={screen.id} className="flex items-center gap-2.5 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editPerms.includes(screen.id)}
                    onChange={() => togglePerm(screen.id)}
                    className="rounded"
                  />
                  <span className="text-gray-700">{screen.label}</span>
                </label>
              ))}
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleSavePerms}
                disabled={updateProfile.isPending}
                className="flex-1 rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {updateProfile.isPending ? "Salvando..." : "Salvar"}
              </button>
              <button
                onClick={() => setEditingProfile(null)}
                className="flex-1 rounded-lg border px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
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
