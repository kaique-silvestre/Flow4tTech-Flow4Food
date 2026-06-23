# PRP — Issue #18: Usuário livre
**GitHub Issue:** #18 | **Type:** AFK | **Depende de:** #15 (done, commit 66bb1fd)

## Contexto

`resolve_permissions` em `auth_service.py:55` já trata `profile_id is None → []`.
Mas `_build_token_response:73` e `rotate_refresh_token:112` usam `user.profile.name` diretamente → crash se profile_id=None.
`_to_response` em `users_service.py:29` também usa `user.profile.name` → crash.

Migration próxima: `0060_`.

---

## Tarefas

### Bloco A — Migration (0060)
- [ ] A1. Criar `backend/alembic/versions/0060_user_permissions_nullable_profile.py`
  - CREATE TABLE `user_permissions`: `id BIGSERIAL PK`, `tenant_id BIGINT server_default RLS`,
    `user_id BIGINT REFERENCES system_users(id) ON DELETE CASCADE`,
    `screen VARCHAR(50) NOT NULL`, `can_access BOOLEAN NOT NULL DEFAULT true`,
    `UNIQUE(user_id, screen)`
  - RLS em `user_permissions`: `ENABLE ROW LEVEL SECURITY` + policy `tenant_id = (NULLIF(current_setting('app.tenant_id',true),''))::bigint`
  - ALTER TABLE `system_users` ALTER COLUMN `profile_id` DROP NOT NULL
  - SQLite guard: `is_pg = conn.dialect.name == "postgresql"`; SQLite não suporta RLS nem BIGSERIAL — usar `AUTOINCREMENT` ou `INTEGER PRIMARY KEY`

### Bloco B — Model + Repository
- [ ] B1. `backend/src/models/user_permissions.py` — `UserPermission(Base)`:
  ```python
  id: Mapped[int] = mapped_column(primary_key=True)
  tenant_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False, server_default=sa.text("(NULLIF(current_setting('app.tenant_id', true), ''))::bigint"))
  user_id: Mapped[int] = mapped_column(sa.ForeignKey("system_users.id", ondelete="CASCADE"), nullable=False)
  screen: Mapped[str] = mapped_column(sa.String(50), nullable=False)
  can_access: Mapped[bool] = mapped_column(nullable=False, server_default="true")
  ```
- [ ] B2. Adicionar `user_permissions: Mapped[list[UserPermission]] = relationship(back_populates="user", cascade="all, delete-orphan")` em `SystemUser`
- [ ] B3. Adicionar `user: Mapped[SystemUser] = relationship(back_populates="user_permissions")` em `UserPermission`
- [ ] B4. `backend/src/repositories/user_permissions_repository.py`:
  - `list_by_user(db, user_id) → list[UserPermission]`
  - `replace_all(db, user_id, screens: list[str]) → list[UserPermission]` — delete all then insert

### Bloco C — Auth Update
- [ ] C1. `auth_service.py:55` — `resolve_permissions` já correto (profile_id None → []). Atualizar para ler `user_permissions`:
  ```python
  def resolve_permissions(user) -> list:
      if user.profile_id is None:
          return [p.screen for p in user.user_permissions if p.can_access]
      profile = user.profile
      if profile.template_id is not None:
          return [p.screen for p in profile.template.permissions if p.can_access]
      return [p.screen for p in profile.permissions if p.can_access]
  ```
- [ ] C2. `_build_token_response:73` — corrigir `user.profile.name` → `user.profile.name if user.profile else None`
  - Payload: `"profile_name": user.profile.name if user.profile else None`
- [ ] C3. `rotate_refresh_token:112` — mesmo fix: `user.profile.name if user.profile else None`

### Bloco D — Schemas + Service
- [ ] D1. `backend/src/schemas/users.py`:
  - `UserCreate.profile_id: Optional[int] = None` (era `int` required)
  - `UserResponse.profile_id: Optional[int]`
  - `UserResponse.profile_name: Optional[str]`
- [ ] D2. `backend/src/schemas/auth.py` — verificar `UserInfo.profile_id` e `profile_name`, tornar Optional se necessário
- [ ] D3. `users_service.py:25` — `_to_response`: `profile_name=user.profile.name if user.profile else None`
- [ ] D4. `users_service.py:53` — `create_new_user`: se `data.profile_id` é None, pular validação de perfil
- [ ] D5. `users_service.py:151` — `_check_not_last_admin`: já seguro (`user.profile_id == admin_profile.id` → False se None)

### Bloco E — API de permissões
- [ ] E1. `backend/src/api/routes/users.py` — adicionar:
  - `GET /api/users/{user_id}/permissions` → `list[str]` (screens com can_access=True)
  - `PUT /api/users/{user_id}/permissions` body `{"screens": list[str]}` → replace_all → retornar `list[str]`
- [ ] E2. Schema: `UserPermissionsUpdate(BaseModel): screens: list[str]`

### Bloco F — Frontend
- [ ] F1. `frontend/src/features/configuracoes/usuarios/useUsers.ts` — adicionar hooks:
  - `useUserPermissions(userId)` → GET `/api/users/{id}/permissions`
  - `useUpdateUserPermissions(userId)` → PUT `/api/users/{id}/permissions`
- [ ] F2. `UserModal.tsx` — campo "Perfil" vira opcional:
  - Zod: `profile_id: z.coerce.number().optional()` (remover `.min(1)`)
  - Select: adicionar `<option value="">Sem perfil fixo</option>` como primeira opção
  - Quando `profile_id` vazio: mostrar seção de checkboxes de telas (buscar lista de screens disponíveis)
  - Quando `profile_id` preenchido: comportamento atual
- [ ] F3. `UserResponse` type em `useUsers.ts`: `profile_id: number | null`, `profile_name: string | null`

### Bloco G — Testes
- [ ] G1. `backend/tests/test_auth.py` ou novo `test_usuario_livre.py`:
  - Criar user sem profile_id → login OK → JWT tem `permissions=[]`
  - Criar user sem profile_id + inserir user_permissions → JWT contém as telas
  - Criar user com profile_id → comportamento igual ao anterior (não regride)
  - G4. rotate_refresh_token com user sem perfil → não crasha

---

## Observações críticas

1. **SQLite testes**: `UserPermission.tenant_id server_default` usa `current_setting` — conftest já patcha isso. `created_at` se adicionado: passar explicitamente nos fixtures.
2. **Relacionamento circular**: `SystemUser` importa de `user_permissions.py`; usar `TYPE_CHECKING` para evitar import circular.
3. **Screens disponíveis no frontend**: precisam de lista hardcoded ou endpoint `/api/screens` — usar lista hardcoded por ora (mesma usada nos templates).
4. **`rotate_refresh_token`**: carrega `user` via `get_user_by_id` — verificar que `users_repository.get_user_by_id` faz `joinedload` em `profile` e `user_permissions`. Se não, adicionar.

---

## Validações

```bash
cd backend && python -m pytest
cd frontend && npm run type-check && npm run lint && npm run build
```

## Commit

```
feat(usuarios): profile_id nullable + user_permissions — closes #18
```
