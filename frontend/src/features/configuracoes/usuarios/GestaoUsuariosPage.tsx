import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { useAuthStore } from "@/stores/authStore";
import {
  useUsers,
  useToggleUserActive,
  type UserResponse,
} from "./useUsers";
import { useProfiles, useToggleProfileActive, type ProfileResponse } from "./useProfiles";
import { UserModal } from "./UserModal";
import { ProfileModal } from "./ProfileModal";

type ConfirmState = {
  open: boolean;
  title: string;
  description?: string;
  confirmLabel?: string;
  action: () => void;
};

type Tab = "usuarios" | "perfis";

export function GestaoUsuariosPage() {
  const [tab, setTab] = useState<Tab>("usuarios");
  const [search, setSearch] = useState("");
  const [filterProfile, setFilterProfile] = useState<number | undefined>();
  const [searchProfiles, setSearchProfiles] = useState("");
  const [showInactiveUsers, setShowInactiveUsers] = useState(false);
  const [showInactiveProfiles, setShowInactiveProfiles] = useState(false);
  const [userModalOpen, setUserModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserResponse | undefined>();
  const [profileModalOpen, setProfileModalOpen] = useState(false);
  const [editingProfile, setEditingProfile] = useState<ProfileResponse | undefined>();
  const [confirmState, setConfirmState] = useState<ConfirmState>({
    open: false,
    title: "",
    action: () => {},
  });

  const currentUser = useAuthStore((s) => s.user);
  const { data: allUsers = [], isLoading: loadingUsers } = useUsers(search || undefined, filterProfile);
  const { data: allProfiles = [] } = useProfiles();
  const toggleActive = useToggleUserActive();
  const toggleProfileActive = useToggleProfileActive();

  const users = showInactiveUsers ? allUsers : allUsers.filter((u) => u.is_active);
  const profiles = allProfiles
    .filter((p) => showInactiveProfiles || p.is_active)
    .filter((p) =>
      !searchProfiles ||
      p.name.toLowerCase().includes(searchProfiles.toLowerCase())
    );

  function openEditUser(user: UserResponse) {
    setEditingUser(user);
    setUserModalOpen(true);
  }

  function openEditProfile(profile: ProfileResponse) {
    setEditingProfile(profile);
    setProfileModalOpen(true);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Gestão de Usuários</h1>
      </div>

      <div className="flex gap-2 border-b">
        <button
          className={`px-4 py-2 text-sm font-medium transition-colors ${tab === "usuarios" ? "border-b-2 border-gray-900 text-gray-900" : "text-gray-500 hover:text-gray-700"}`}
          onClick={() => setTab("usuarios")}
        >
          Usuários
        </button>
        <button
          className={`px-4 py-2 text-sm font-medium transition-colors ${tab === "perfis" ? "border-b-2 border-gray-900 text-gray-900" : "text-gray-500 hover:text-gray-700"}`}
          onClick={() => setTab("perfis")}
        >
          Perfis
        </button>
      </div>

      {tab === "usuarios" && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 flex-wrap">
            <Input
              placeholder="Buscar por nome ou usuário..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="max-w-xs"
            />
            <select
              className="rounded border px-3 py-2 text-sm"
              value={filterProfile ?? ""}
              onChange={(e) => setFilterProfile(e.target.value ? Number(e.target.value) : undefined)}
            >
              <option value="">Todos os perfis</option>
              {allProfiles.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
            <label className="flex items-center gap-1.5 text-sm text-gray-600 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={showInactiveUsers}
                onChange={(e) => setShowInactiveUsers(e.target.checked)}
                className="rounded"
              />
              Mostrar inativos
            </label>
            <Button
              className="ml-auto"
              onClick={() => { setEditingUser(undefined); setUserModalOpen(true); }}
            >
              + Cadastrar Usuário
            </Button>
          </div>

          {loadingUsers ? (
            <p className="text-sm text-gray-500">Carregando...</p>
          ) : users.length === 0 ? (
            <div className="py-12 text-center text-gray-500">
              <p>Nenhum usuário encontrado</p>
              <Button className="mt-4" onClick={() => { setEditingUser(undefined); setUserModalOpen(true); }}>
                + Cadastrar primeiro usuário
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto rounded border">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
                  <tr>
                    <th className="px-4 py-3">Nome</th>
                    <th className="px-4 py-3">Usuário</th>
                    <th className="px-4 py-3">Email</th>
                    <th className="px-4 py-3">Perfil</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {users.map((user) => {
                    const isSelf = currentUser?.user_id === user.id;
                    return (
                      <tr key={user.id} className={`hover:bg-gray-50 ${!user.is_active ? "opacity-60" : ""}`}>
                        <td className="px-4 py-3 font-medium">{user.name}</td>
                        <td className="px-4 py-3 text-gray-600">{user.username}</td>
                        <td className="px-4 py-3 text-gray-600">{user.email ?? "—"}</td>
                        <td className="px-4 py-3">{user.profile_name}</td>
                        <td className="px-4 py-3">
                          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${user.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                            {user.is_active ? "Ativo" : "Inativo"}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <Button variant="ghost" size="sm" onClick={() => openEditUser(user)}>
                              Editar
                            </Button>
                            {!isSelf && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className={user.is_active ? "text-red-600 hover:text-red-700 hover:bg-red-50" : ""}
                                onClick={() => {
                                  const isDeactivating = user.is_active;
                                  setConfirmState({
                                    open: true,
                                    title: isDeactivating
                                      ? `Desativar "${user.name}"?`
                                      : `Ativar "${user.name}"?`,
                                    description: isDeactivating
                                      ? "O usuário perderá acesso ao sistema. É possível reativar depois."
                                      : "O usuário voltará a ter acesso ao sistema.",
                                    confirmLabel: isDeactivating ? "Desativar" : "Ativar",
                                    action: () => toggleActive.mutate(user.id),
                                  });
                                }}
                              >
                                {user.is_active ? "Desativar" : "Ativar"}
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === "perfis" && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 flex-wrap">
            <Input
              placeholder="Buscar por nome..."
              value={searchProfiles}
              onChange={(e) => setSearchProfiles(e.target.value)}
              className="max-w-xs"
            />
            <label className="flex items-center gap-1.5 text-sm text-gray-600 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={showInactiveProfiles}
                onChange={(e) => setShowInactiveProfiles(e.target.checked)}
                className="rounded"
              />
              Mostrar inativos
            </label>
            <Button className="ml-auto" onClick={() => { setEditingProfile(undefined); setProfileModalOpen(true); }}>
              + Novo Perfil
            </Button>
          </div>
          <div className="overflow-x-auto rounded border">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
                <tr>
                  <th className="px-4 py-3">Nome</th>
                  <th className="px-4 py-3">Usuários</th>
                  <th className="px-4 py-3">Permissões</th>
                  <th className="px-4 py-3">Sistema</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {profiles.map((profile) => (
                  <tr key={profile.id} className={`hover:bg-gray-50 ${!profile.is_active ? "opacity-60" : ""}`}>
                    <td className="px-4 py-3 font-medium">{profile.name}</td>
                    <td className="px-4 py-3">{profile.user_count}</td>
                    <td className="px-4 py-3">{profile.permissions.length}/8</td>
                    <td className="px-4 py-3">{profile.is_system ? "✓" : "—"}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${profile.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                        {profile.is_active ? "Ativo" : "Inativo"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="min-w-[4.5rem]"
                          onClick={() => openEditProfile(profile)}
                        >
                          {profile.name === "Admin" ? "Ver" : "Editar"}
                        </Button>
                        {(() => {
                          const isAdmin = profile.name === "Admin";
                          const hasUsers = profile.user_count > 0;
                          const canToggle = !isAdmin && !hasUsers;
                          const isDeactivating = profile.is_active;
                          return (
                            <Button
                              variant="ghost"
                              size="sm"
                              disabled={!canToggle}
                              className={canToggle && isDeactivating ? "text-red-600 hover:text-red-700 hover:bg-red-50" : ""}
                              onClick={canToggle ? () => {
                                setConfirmState({
                                  open: true,
                                  title: isDeactivating
                                    ? `Desativar perfil "${profile.name}"?`
                                    : `Ativar perfil "${profile.name}"?`,
                                  description: isDeactivating
                                    ? "O perfil ficará indisponível para novos usuários."
                                    : "O perfil voltará a estar disponível para novos usuários.",
                                  confirmLabel: isDeactivating ? "Desativar" : "Ativar",
                                  action: () => toggleProfileActive.mutate(profile.id),
                                });
                              } : undefined}
                            >
                              {isDeactivating ? "Desativar" : "Ativar"}
                            </Button>
                          );
                        })()}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <UserModal
        open={userModalOpen}
        onClose={() => { setUserModalOpen(false); setEditingUser(undefined); }}
        user={editingUser}
      />
      <ProfileModal
        open={profileModalOpen}
        onClose={() => { setProfileModalOpen(false); setEditingProfile(undefined); }}
        profile={editingProfile}
      />
      <ConfirmDialog
        open={confirmState.open}
        title={confirmState.title}
        description={confirmState.description}
        confirmLabel={confirmState.confirmLabel}
        onConfirm={() => {
          confirmState.action();
          setConfirmState((s) => ({ ...s, open: false }));
        }}
        onCancel={() => setConfirmState((s) => ({ ...s, open: false }))}
      />
    </div>
  );
}
