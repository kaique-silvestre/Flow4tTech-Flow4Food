# PRP — Issue #16: Painel admin tenants + assinaturas
**GitHub Issue:** #16 | **Type:** AFK | **Depende de:** #12

## Contexto

`get_platform_db()` e `require_platform_admin` já existem (`database.py`, `dependencies.py`).
`platform_auth.py` usa padrão `_public_router` (sem auth) + `router` (com `Depends(require_platform_admin)`), ambos montados em `/api/platform`.
Models: `Tenant` (tenants), `Assinatura` (assinaturas), `SystemUser` (system_users).
Testes: padrão de `test_platform_auth.py` — engine SQLite próprio, override `get_db` + `get_platform_db`, seed manual.

## Gotchas

- Queries usam `get_platform_db()` — NUNCA `get_db()` / `get_tenant_db()`
- `Tenant.created_at` tem `server_default=NOW()` — passar explícito em fixtures SQLite
- `Assinatura.created_at` e `updated_at` têm `server_default=NOW()` — idem
- `SystemUser.created_at`/`updated_at` — idem
- `Assinatura.tenant_id` único (1:1 com Tenant)
- Status assinatura válidos: `"trial"`, `"ativa"`, `"suspensa"`, `"cancelada"`
- Novos endpoints adicionados ao `platform_auth.router` (já tem `Depends(require_platform_admin)`) — não criar router separado

## Tarefas

### Bloco A — Repository
- [ ] A1. Criar `backend/src/repositories/platform_repository.py`:
  - `list_tenants(db, status_filter=None)` → list de dicts com `id, nome_fantasia, cnpj, status_tenant, status_assinatura, data_vencimento`
    - LEFT JOIN assinaturas (tenant pode não ter assinatura ainda)
  - `get_tenant_users(db, tenant_id)` → list de dicts com `id, name, username, profile_name, last_login, is_active`
    - JOIN profiles p/ nome do perfil
  - `update_assinatura_status(db, tenant_id, new_status)` → Assinatura atualizada (upsert: criar se não existir)

### Bloco B — API (adicionar ao `platform_auth.py` no `router` protegido)
- [ ] B1. Schemas Pydantic inline em `platform_auth.py` (ou em `src/schemas/platform.py`):
  - `TenantListItem`, `TenantUserItem`, `AssinaturaStatusUpdate`
- [ ] B2. `GET /api/platform/tenants?status=` → lista `TenantListItem`
- [ ] B3. `GET /api/platform/tenants/{tenant_id}/users` → lista `TenantUserItem`
- [ ] B4. `PATCH /api/platform/tenants/{tenant_id}/assinatura` body `{"status": "ativa"|"suspensa"|"cancelada"|"trial"}`
- [ ] B5. Todos com `db: Session = Depends(get_platform_db)`

### Bloco C — Frontend
- [ ] C1. `frontend/src/stores/platformAuthStore.ts` — Zustand + persist(`"platform-auth"`)
  - `PlatformUser { admin_id, email, name, platform_admin: true }`
  - `token`, `user`, `setToken`, `clearToken`
- [ ] C2. `frontend/src/components/auth/RequirePlatformAuth.tsx` — guard que redireciona `/platform/login`
- [ ] C3. `frontend/src/features/platform/PlatformLoginPage.tsx` — form email+senha, POST `/api/platform/auth/login`, `setToken`
- [ ] C4. `frontend/src/features/platform/PlatformLayout.tsx` — layout simples (header "Flow4Tech Admin", sem sidebar de tenant)
- [ ] C5. `frontend/src/features/platform/PlatformTenantsPage.tsx`:
  - Tabela: nome_fantasia, cnpj, status_tenant, status_assinatura, data_vencimento, ações
  - Filtro por status assinatura (select)
  - Botões Ativar/Suspender (PATCH assinatura)
  - Clique na linha → navega para `/platform/tenants/:id`
- [ ] C6. `frontend/src/features/platform/PlatformTenantDetailPage.tsx`:
  - Título com nome do tenant
  - Tabela: name, username, profile_name, last_login, is_active
- [ ] C7. Hook `frontend/src/features/platform/usePlatformApi.ts`:
  - `useTenants(statusFilter?)`, `useTenantUsers(tenantId)`, `useUpdateAssinatura()`
  - Auth header de `platformAuthStore`
- [ ] C8. `App.tsx`: adicionar rotas `/platform/login`, `/platform/tenants`, `/platform/tenants/:id`
  - Rotas protegidas envolvidas em `RequirePlatformAuth`
  - Layout `PlatformLayout` para as páginas protegidas

### Bloco D — Testes (`backend/tests/test_platform_tenants.py`)
- [ ] D1. `GET /platform/tenants` retorna lista com todos os tenants (sem filtro)
- [ ] D2. `GET /platform/tenants?status=trial` filtra por status assinatura
- [ ] D3. `GET /platform/tenants/{id}/users` retorna usuários do tenant
- [ ] D4. `PATCH /platform/tenants/{id}/assinatura` atualiza status → GET confirma mudança
- [ ] D5. JWT de tenant (`tenant_id` no payload) rejeitado com 403 em todos os endpoints
- [ ] D6. Sem token → 401

## Ordem de execução

A1 → B1-B5 → D1-D6 → C1-C8

## Validações

```bash
cd backend && python -m pytest
cd frontend && npm run type-check && npm run lint && npm run build
```
