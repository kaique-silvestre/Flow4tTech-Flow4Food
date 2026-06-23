# PRP — Issue #11: Templates de perfil
**GitHub Issue:** #11 | **Type:** HITL

## Contexto do codebase (lido)
- `backend/src/models/profiles.py` — `Profile` e `ProfilePermission`. PKs como `mapped_column(primary_key=True)` sem tipo. `tenant_id` BigInteger com `server_default` RLS. `created_at` server_default NOW().
- `backend/src/repositories/profiles_repository.py` — funções puras `(db, ...)`, sem classe.
- `backend/src/services/profiles_service.py` — camada service traduz model→schema, valida tenant/Admin.
- `backend/src/api/routes/profiles.py` — router prefixado, usa `get_tenant_db` + `require_permission("gestao_usuarios")`.
- `backend/src/schemas/profiles.py` — `VALID_SCREENS` lista canônica de telas.
- `backend/alembic/versions/0055_*.py` — revision string `"0055"`, próxima = `"0056"`, `down_revision = "0055"`.
- `backend/tests/conftest.py` — patcha `tenant_id` server_default p/ SQLite. Tests CRUD usam engine SQLite próprio (ver `test_itens.py`): `StaticPool`, `Base.metadata.create_all`, override `get_db` + `get_current_user`.
- `frontend/src/features/configuracoes/usuarios/` — `ProfileModal.tsx` (checkboxes telas), `useProfiles.ts` (hooks React Query). Telas hardcoded em `SCREENS`.

## Gotchas (CLAUDE.md + memória)
- PK sem tipo (`mapped_column(primary_key=True)`) p/ SQLite autoincrement.
- `created_at` explícito em fixtures (server_default NOW() falha no SQLite).
- Toda tabela nova com RLS precisa `tenant_id` server_default RLS — MAS `permission_templates`/`template_permissions` têm linhas `is_system` globais. Decisão: templates de sistema têm `tenant_id` NULL (visíveis a todos); custom têm tenant_id. `conftest` já patcha tenant_id.
- Migration reversível: `downgrade()` dropa tabelas + coluna na ordem inversa (FK primeiro).

## Tarefas

### Bloco A — Migration 0056
- [ ] A1. CREATE TABLE permission_templates (id BIGSERIAL PK, tenant_id BIGINT NULL com server_default RLS, nome VARCHAR(60) NOT NULL, descricao VARCHAR(200) NULL, is_system BOOLEAN DEFAULT FALSE)
- [ ] A2. CREATE TABLE template_permissions (template_id BIGINT FK→permission_templates ondelete CASCADE, screen VARCHAR(50), can_access BOOLEAN DEFAULT TRUE, PRIMARY KEY (template_id, screen))
- [ ] A3. ALTER TABLE profiles ADD COLUMN template_id BIGINT NULL REFERENCES permission_templates(id)
- [ ] A4. Seed: p/ cada perfil `is_system=TRUE` existente (Admin, Gerente, Caixa) → criar template `is_system=TRUE` (tenant_id NULL) com mesmo nome → popular `template_permissions` a partir de `profile_permissions` daquele perfil → setar `profiles.template_id`. Usar `op.get_bind()` + SQL inline.
- [ ] A5. downgrade(): drop FK col profiles.template_id → drop template_permissions → drop permission_templates

### Bloco B — Models
- [ ] B1. `PermissionTemplate` (id, tenant_id Optional, nome, descricao Optional, is_system) + relationship `permissions`
- [ ] B2. `TemplatePermission` (template_id PK+FK, screen PK, can_access) + relationship `template`. PK composta via `primary_key=True` em ambas colunas.
- [ ] B3. `Profile.template_id: Mapped[Optional[int]]` FK + relationship `template`

### Bloco C — Repository (`profiles_repository.py` ou novo `templates_repository.py`)
- [ ] C1. `list_templates(db, tenant_id)` → is_system (tenant NULL) + custom do tenant
- [ ] C2. `create_template(db, tenant_id, nome, descricao, screens)` → custom
- [ ] C3. `assign_template(db, profile_id, template_id | None)`
- [ ] C4. `get_template_screens(db, template_id)` → list[str]

### Bloco D — API (novo `routes/permission_templates.py`, registrar no router principal)
- [ ] D1. GET /api/permission-templates
- [ ] D2. POST /api/permission-templates
- [ ] D3. PATCH /api/permission-templates/{id}
- [ ] D4. DELETE /api/permission-templates/{id} → bloquear `is_system=True` (409)
- [ ] D5. PATCH /api/profiles/{id}/template → body `{template_id: int | null}`
- Guard: `require_permission("gestao_usuarios")`. Schemas em `schemas/permission_templates.py`.

### Bloco E — Frontend
- [ ] E1. Seletor de template na edição de perfil (`ProfileModal.tsx`)
- [ ] E2. Checkboxes read-only quando `template_id` ativo (preenche telas do template)
- [ ] E3. Botão "Personalizar" → PATCH template null → libera checkboxes
- [ ] E4. Hook `usePermissionTemplates()` em `usePermissionTemplates.ts`

### Bloco F — Testes (`tests/test_permission_templates.py`, padrão engine de `test_itens.py`)
- [ ] F1. Criar template → associar a perfil → confirmar `profile.template_id`
- [ ] F2. DELETE template `is_system=True` → 409
- [ ] F3. Migration reversível (upgrade→downgrade smoke, ou assert metadata)

## Validações
- `cd backend && python -m pytest`
- `cd frontend && npm run type-check && npm run lint && npm run build`
