# Issue #25 — Platform Admin Panel (Back-office Flow4Tech)

## Objetivo
Redesenho completo do painel `/platform/*`: gestão de tenants, usuários, perfis, feature flags, impersonation, cockpit, comunicados, auditoria, bloqueio por assinatura.

## Estado Inicial
Já existe:
- Login platform admin + JWT
- Listagem básica de tenants (sem qtd_users, sem criação)
- Detalhe tenant: só lista usuários (read-only)
- `require_active_subscription` dependency (parcial — não checa trial vencido)
- Migração: última = 0071

## Acceptance Criteria
- [ ] AC1: 7 novas tabelas migradas: `platform_settings`, `assinatura_history`, `tenant_features`, `platform_announcements`, `announcement_targets`, `announcement_reads`, `audit_logs`
- [ ] AC2: `POST /api/platform/tenants` — cria tenant + assinatura trial automática
- [ ] AC3: `GET/PATCH /api/platform/settings/{key}` — configurações globais (trial_duration_days=14)
- [ ] AC4: Tenant list: colunas ID, Nome, CNPJ, Status Tenant, Status Assinatura, Vencimento, Qtd Usuários (atual/max)
- [ ] AC5: Bloqueio 402 — middleware verifica `data_vencimento` da assinatura trial e bloqueia se vencida
- [ ] AC6: Feature flags por tenant — CRUD + enforcement (módulo desabilitado → 403 no endpoint)
- [ ] AC7: `PATCH /api/platform/tenants/{id}` — atualiza dados + max_users + data_vencimento
- [ ] AC8: `POST/PATCH /api/platform/tenants/{id}/users` — criar/editar usuário de tenant
- [ ] AC9: `GET/PATCH /api/platform/tenants/{id}/profiles` — listar/editar permissões de perfil
- [ ] AC10: `POST /api/platform/tenants/{id}/users/{uid}/impersonate` — JWT com claim `impersonated_by`, TTL 2h
- [ ] AC11: `GET /api/platform/cockpit` — métricas agregadas (reusa lógica do issue #29)
- [ ] AC12: `GET/POST/PATCH /api/platform/announcements` — comunicados com broadcast/target
- [ ] AC13: `GET /api/platform/audit-logs` — log com filtros
- [ ] AC14: Frontend: PlatformLayout com sidebar (Empresas, Cockpit, Comunicados, Auditoria)
- [ ] AC15: Frontend: Tenant detail com abas Dados / Usuários / Perfis / Feature Flags
- [ ] AC16: Frontend: Banner impersonation no Topbar do tenant + encerrar sessão
- [ ] AC17: Testes: bloqueio 402, feature flags 403, impersonation, comunicados
- [ ] AC18: `GET /api/platform/tenants/{id}/assinatura/historico` — histórico de mudanças

## Tasks por Iteração

### ITERAÇÃO 1 — Migrations + Models
- [ ] I1-A1: Migration 0072 — `platform_settings` (id, key VARCHAR(100) unique, value TEXT, updated_at)
  - INSERT seed: `trial_duration_days = 14`
- [ ] I1-A2: Migration 0073 — `assinatura_history` (id, assinatura_id FK, from_status, to_status, changed_by INT nullable, created_at)
- [ ] I1-A3: Migration 0074 — `tenant_features` (id, tenant_id FK, feature VARCHAR(50), enabled BOOL, updated_at)
  - UniqueConstraint(tenant_id, feature)
- [ ] I1-A4: Migration 0075 — `platform_announcements` (id, title, body TEXT, expires_at nullable, target VARCHAR(10) default 'all', created_by INT nullable, is_active BOOL, created_at)
- [ ] I1-A5: Migration 0076 — `announcement_targets` (id, announcement_id FK CASCADE, tenant_id FK)
- [ ] I1-A6: Migration 0077 — `announcement_reads` (id, announcement_id FK CASCADE, user_id FK CASCADE, read_at)
  - UniqueConstraint(announcement_id, user_id)
- [ ] I1-A7: Migration 0078 — `audit_logs` (id, tenant_id INT nullable, user_id INT nullable, action VARCHAR(100), entity VARCHAR(100), entity_id INT nullable, before JSONB nullable, after JSONB nullable, impersonated_by INT nullable, created_at)
  - NOTA: JSONB no PG, usar sa.Text() no SQLite-compat (guard na migration para JSONB)
- [ ] I1-B1: Model `PlatformSettings` em `backend/src/models/platform_settings.py`
- [ ] I1-B2: Model `AssinaturaHistory` em `backend/src/models/assinaturas.py` (same file)
- [ ] I1-B3: Model `TenantFeature` em `backend/src/models/tenant_features.py`
- [ ] I1-B4: Models `PlatformAnnouncement`, `AnnouncementTarget`, `AnnouncementRead` em `backend/src/models/announcements.py`
- [ ] I1-B5: Model `AuditLog` em `backend/src/models/audit_logs.py`
- [ ] I1-C1: Registrar todos os novos models em `backend/src/models/__init__.py`

### ITERAÇÃO 2 — Backend: Platform Settings + Tenant Create + Subscription Blocking
- [ ] I2-A1: `platform_repository.get_setting(db, key)` + `upsert_setting(db, key, value)`
- [ ] I2-A2: `platform_repository.create_platform_tenant(db, data)` — cria Tenant + Assinatura trial com data_vencimento
- [ ] I2-A3: Atualizar `platform_repository.list_tenants()` — adicionar `qtd_usuarios` + `max_users` (subquery COUNT SystemUser)
- [ ] I2-A4: `platform_repository.update_assinatura_status()` — gravar `AssinaturaHistory` ao mudar status
- [ ] I2-A5: `platform_repository.get_assinatura_history(db, tenant_id)`
- [ ] I2-B1: Schemas inline em `platform_auth.py`:
  - `PlatformTenantCreate` (nome_fantasia, cnpj, endereco, telefone, max_users, trial_days optional)
  - `TenantListItem` atualizado (qtd_usuarios, max_users)
  - `PlatformSettingResponse`, `PlatformSettingUpdate`
  - `AssinaturaHistoryItem`
- [ ] I2-B2: Endpoints `POST /tenants`, `GET /settings`, `PATCH /settings/{key}`, `GET /tenants/{id}/assinatura/historico`
- [ ] I2-C1: Expandir `require_active_subscription` em `dependencies.py`:
  - Checar `subscription_status` no payload (se trial, verificar `trial_expires_at`)
  - Alternativa: middleware que checa DB a cada request (melhor: encode no JWT)
  - Decisão: incluir `trial_expires_at` no JWT payload no login de tenant; verificar no `require_active_subscription`
- [ ] I2-C2: Atualizar `auth_service.create_tenant_token()` para incluir `trial_expires_at` no payload

### ITERAÇÃO 3 — Backend: Tenant CRUD + User/Profile CRUD + Feature Flags
- [ ] I3-A1: `PATCH /api/platform/tenants/{id}` — atualiza nome, cnpj, endereco, telefone, max_users, status, data_vencimento
- [ ] I3-A2: `GET /api/platform/tenants/{id}` — detalhe completo do tenant (nome, cnpj, status, max_users, assinatura, created_at)
- [ ] I3-B1: `platform_repository.create_tenant_user(db, tenant_id, data)`
- [ ] I3-B2: `platform_repository.update_tenant_user(db, tenant_id, user_id, data)`
- [ ] I3-B3: `platform_repository.get_tenant_profiles(db, tenant_id)` com permissões
- [ ] I3-B4: `platform_repository.update_tenant_profile(db, tenant_id, profile_id, permissions, is_active)`
- [ ] I3-C1: `platform_repository.get_tenant_features(db, tenant_id)` 
- [ ] I3-C2: `platform_repository.upsert_tenant_features(db, tenant_id, features: dict[str, bool])`
- [ ] I3-D1: Endpoints:
  - `GET /api/platform/tenants/{id}` — detalhe
  - `PATCH /api/platform/tenants/{id}` — update
  - `POST /api/platform/tenants/{id}/users` — criar user
  - `PATCH /api/platform/tenants/{id}/users/{uid}` — editar user
  - `GET /api/platform/tenants/{id}/profiles` — listar perfis com permissões
  - `PATCH /api/platform/tenants/{id}/profiles/{pid}` — editar permissões
  - `GET /api/platform/tenants/{id}/features` — flags
  - `PUT /api/platform/tenants/{id}/features` — atualizar flags
- [ ] I3-E1: `require_feature(feature_name)` dependency em `dependencies.py` (verifica TenantFeature na DB)

### ITERAÇÃO 4 — Backend: Impersonation + Cockpit + Announcements + Audit + Tests
- [ ] I4-A1: `POST /api/platform/tenants/{id}/users/{uid}/impersonate` — JWT com `impersonated_by`, exp=2h
- [ ] I4-B1: `platform_repository.get_cockpit_metrics(db)` — raw SQL (reutilizar lógica issue #29 se existir)
- [ ] I4-B2: Endpoint `GET /api/platform/cockpit`
- [ ] I4-C1: `platform_repository.list_announcements(db)`, `create_announcement`, `update_announcement`
- [ ] I4-C2: Endpoints `GET/POST/PATCH /api/platform/announcements`
- [ ] I4-C3: Endpoint público (autenticado como tenant) `GET /api/app/announcements` — filtra por tenant + não expirado
- [ ] I4-C4: Endpoint `POST /api/app/announcements/{id}/read`
- [ ] I4-D1: `audit_service.log()` — fire-and-forget com BackgroundTasks
- [ ] I4-D2: Endpoint `GET /api/platform/audit-logs` com filtros
- [ ] I4-E1: Tests `test_platform_admin_panel.py`:
  - Tenant create + trial
  - Subscription block (402)
  - Feature flag enforcement (403)
  - Impersonation token
  - Announcements

### ITERAÇÃO 5 — Frontend: Platform UI Redesign + Tenant List
- [ ] I5-A1: Redesenhar `PlatformLayout.tsx` — sidebar com navegação (Empresas, Cockpit, Comunicados, Auditoria)
- [ ] I5-A2: Atualizar `PlatformTenantsPage.tsx` — colunas completas + botão "Nova Empresa"
- [ ] I5-A3: `CreateTenantModal.tsx` — form com campos do PRD
- [ ] I5-A4: Atualizar `usePlatformApi.ts` — `useCreateTenant`, `usePlatformSettings`, `useUpdateSetting`

### ITERAÇÃO 6 — Frontend: Tenant Detail Tabs (Dados + Usuários + Perfis + Feature Flags)
- [ ] I6-A1: Redesenhar `PlatformTenantDetailPage.tsx` com tabs: Dados, Usuários, Perfis, Feature Flags
- [ ] I6-A2: Aba Dados — form editável (nome, cnpj, endereço, telefone, max_users, status assinatura, data_vencimento) + histórico de status
- [ ] I6-A3: Aba Usuários — tabela com create/edit inline ou modal; indicador X/max_users
- [ ] I6-A4: Aba Perfis — tabela de perfis com permissões em checkboxes
- [ ] I6-A5: Aba Feature Flags — toggles por módulo
- [ ] I6-B1: Atualizar `usePlatformApi.ts` — hooks para tenant detail, users CRUD, profiles, features

### ITERAÇÃO 7 — Frontend: Cockpit + Comunicados + Impersonation Banner + Audit Log
- [ ] I7-A1: `PlatformCockpitPage.tsx` — tabela com métricas por tenant, sort, filtro
- [ ] I7-A2: `PlatformAnnouncementsPage.tsx` — criar/listar comunicados
- [ ] I7-A3: `PlatformAuditLogPage.tsx` — log com filtros
- [ ] I7-B1: Banner impersonation no `Topbar.tsx` — verifica campo `impersonation` no JWT; mostra "Sessão de suporte — admin@flow4tech.com" + botão encerrar
- [ ] I7-B2: Botão "Entrar como" na aba Usuários do tenant detail

### ITERAÇÃO 8 — Final Validation + Commit
- [ ] I8-A1: `cd backend && python -m pytest tests/ -x -q` — todos PASS
- [ ] I8-A2: `cd frontend && npm run type-check` — zero erros
- [ ] I8-A3: `cd frontend && npm run lint` — zero erros meus
- [ ] I8-A4: Commit único com mensagem descritiva

## Padrões do Codebase
- Models SEM `from __future__ import annotations` + Optional[X] (exceto assinaturas.py e tenants.py que têm)
- PK: `mapped_column(primary_key=True)` SEM tipo
- `server_default=sa.text("NOW()")` para timestamps
- JSONB SQLite-compat: usar `sa.Text()` no model + guard PG na migration
- Migration revision curta, sem guards PG p/ add_column simples
- Platform routes: `router = APIRouter(dependencies=[Depends(require_platform_admin)])` + `db: Session = Depends(get_platform_db)`
- Schemas Pydantic inline no arquivo de routes (padrão platform_auth.py)
- Tests: SQLite in-memory, StaticPool, override `get_db` E `get_platform_db`
- `auth_service.create_access_token(payload)` — aceita dict, usa JWT_SECRET
- `hash_password()` e `bcrypt.checkpw()` para senhas

## Notas Críticas
- `tenant_features` table: não usar ARRAY PG — uma linha por feature (tenant_id, feature, enabled)
- AssinaturaHistory: gravada ao mudar status, não via trigger
- Impersonation: claim extras no JWT `impersonated_by`, `impersonation: True`, exp=2h fixo não renovável
- Audit log: BackgroundTasks do FastAPI (fire-and-forget)
- Feature flag enforcement: `require_feature("compras")` etc. como dependency FastAPI
- `platform_settings` seed: `INSERT INTO platform_settings (key, value) VALUES ('trial_duration_days', '14') ON CONFLICT DO NOTHING`
