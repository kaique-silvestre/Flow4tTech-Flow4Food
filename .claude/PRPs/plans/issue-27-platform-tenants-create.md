# Issue #27 — Lista de Empresas Melhorada + Criar Tenant

## Objetivo
Expandir listagem de tenants na plataforma com colunas completas + modal de criação.
Criar tabela `platform_settings` com seed `trial_duration_days = 14`.

## Acceptance Criteria
- [ ] Tabela lista: ID, Nome Fantasia, CNPJ, Status Tenant, Status Assinatura, Vencimento, Qtd Usuários (X/max)
- [ ] Filtro por status de assinatura funcional
- [ ] Botão "Nova Empresa" abre modal com campos: nome fantasia (obrigatório), CNPJ, endereço, telefone, max_users, dias de trial (default vem de platform_settings)
- [ ] Empresa criada recebe assinatura `trial` com `data_vencimento = agora + trial_days`
- [ ] Migration cria tabela `platform_settings` com seed `trial_duration_days = 14`
- [ ] Endpoints: `POST /api/platform/tenants`, `GET /api/platform/settings`, `PATCH /api/platform/settings`
- [ ] Clicar na linha navega para `/platform/tenants/:id`

## Tasks

### A — Backend: Migration + Model
- [ ] A1: Migration 0072 — cria `platform_settings` (id, key, value, updated_at) + INSERT trial_duration_days=14
- [ ] A2: Model `PlatformSettings` em `backend/src/models/platform_settings.py`
- [ ] A3: Registrar em `backend/src/models/__init__.py`

### B — Backend: Repository
- [ ] B1: Funções em `platform_repository.py`:
  - `get_setting(db, key) -> str | None`
  - `upsert_setting(db, key, value) -> PlatformSettings`
  - Atualizar `list_tenants()` para incluir `qtd_usuarios` + `max_users` (subquery COUNT SystemUser por tenant)
  - `create_platform_tenant(db, data) -> Tenant + Assinatura`

### C — Backend: Schemas + Routes
- [ ] C1: Schemas em `platform_auth.py` (Pydantic inline ou arquivo separado):
  - `PlatformTenantCreate` (nome_fantasia, cnpj, endereco, telefone, max_users, trial_days)
  - `PlatformSettingResponse` (key, value)
  - `PlatformSettingUpdate` (value)
  - Atualizar `TenantListItem` com `qtd_usuarios: int`, `max_users: int`
- [ ] C2: Novos endpoints em `platform_auth.py`:
  - `POST /tenants` — cria tenant + trial assinatura
  - `GET /settings` — lista todas as settings
  - `PATCH /settings/{key}` — atualiza uma setting

### D — Frontend: usePlatformApi.ts
- [ ] D1: Atualizar `TenantListItem` com `qtd_usuarios: number`, `max_users: number`
- [ ] D2: `useCreateTenant` mutation — `POST /api/platform/tenants`
- [ ] D3: `usePlatformSettings` query — `GET /api/platform/settings`
- [ ] D4: `useUpdateSetting` mutation — `PATCH /api/platform/settings/{key}`

### E — Frontend: UI
- [ ] E1: `CreateTenantModal.tsx` em `frontend/src/features/platform/`
  - Campos: nome_fantasia (obrigatório), CNPJ, endereço, telefone, max_users, dias_trial (default de settings)
  - Submit → POST /api/platform/tenants → invalidate platform-tenants
- [ ] E2: Atualizar `PlatformTenantsPage.tsx`:
  - Adicionar colunas: ID, Qtd Usuários (X/max)
  - Botão "Nova Empresa" → abre CreateTenantModal
  - Clicar na linha → navigate (já existe, confirmar)

## Validações
```bash
cd backend && source .venv/bin/activate && python -m pytest tests/ -x -q 2>&1 | tail -20
cd frontend && npm run type-check 2>&1 | tail -20
cd frontend && npm run lint 2>&1 | tail -20
```
