---
iteration: 1
max_iterations: 10
status: COMPLETE
plan_path: ".claude/PRPs/plans/issue-11-templates-permissao.md"
started_at: "2026-06-10T00:00:00Z"
---

# Ralph Progress Log

## Codebase Patterns
- Models SEM `from __future__ import annotations`: usar `Optional[X]` (SQLAlchemy compat Py3.9). Models COM future annotations: usar `X | None` (ruff UP045).
- PK SQLite-compat: `mapped_column(primary_key=True)` SEM tipo (não `sa.BigInteger()`).
- `created_at`/`server_default NOW()` falha no SQLite ao inserir — passar valor explícito em fixtures/services.
- tenant_id RLS server_default; conftest patcha p/ SQLite (`DefaultClause(sa.text("1"))`).
- Migration: revision string curta, `op.get_bind().dialect.name == 'postgresql'` para guards PG-only.
- Tests CRUD: engine SQLite próprio (StaticPool, create_all/drop_all), override BOTH `get_db` + `get_current_user` (ver test_itens.py).
- Frontend: hooks React Query em features/configuracoes/usuarios; toast em `@/lib/toast`; api em `@/lib/api`.
- profiles_repository: funções puras `(db, ...)`, sem classe.

## Iteration 1 - 2026-06-10 (Issue #11 COMPLETE)

### Completed (todos os blocos A-F)
- Migration 0056: permission_templates + template_permissions (PK composta) + profiles.template_id (FK SET NULL) + seed espelhando perfis is_system → templates de sistema (tenant_id NULL)
- Models: PermissionTemplate, TemplatePermission, Profile.template_id + relationships (profiles.py)
- Repository: templates_repository.py (list/get/create/update/delete/get_template_screens/assign)
- Service: templates_service.py (_get_owned visibility guard, bloqueio is_system em update/delete)
- API: routes/permission_templates.py (GET/POST/PATCH/DELETE) + PATCH /api/profiles/{id}/template; registrado em main.py
- Schemas: permission_templates.py + template_id em ProfileResponse
- Frontend: usePermissionTemplates.ts (query + assign mutation), template_id em ProfileResponse TS, ProfileModal.tsx (seletor + checkboxes locked + botão Personalizar)
- Tests: tests/test_permission_templates.py (5 testes: F1 criar+assign, list sys+custom, F2 delete sys 409, unassign null, F3 tables roundtrip)
- Commits: 3941654 (backend), 72201bf (frontend)

### Validation Status
- Ruff: PASS (arquivos da issue)
- Backend pytest: 173 pass / 4 skip / 0 fail
- Frontend type-check: PASS
- Frontend lint: PASS (max-warnings 0)
- Frontend build: PASS (8.40s; chunk-size warning pré-existente)

### Learnings
- Profile.created_at/updated_at usam server_default NOW() → seeds de Profile em testes SQLite DEVEM passar created_at/updated_at explícitos
- Templates de sistema = tenant_id NULL (globais), visíveis a todos os tenants; custom = tenant_id do tenant
- PK composta em modelo: dois `mapped_column(primary_key=True)` (template_id FK + screen)
- billing.py tem erros ruff UP045 pré-existentes (não commitados, fora do escopo #11) — não tocar
