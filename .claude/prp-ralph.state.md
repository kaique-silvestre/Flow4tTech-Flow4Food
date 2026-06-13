---
iteration: 1
max_iterations: 8
plan_path: ".claude/PRPs/plans/issue-25-platform-admin-panel.md"
started_at: "2026-06-13T03:00:00Z"
status: COMPLETE
---

# Ralph Progress Log

## Codebase Patterns
- Models SEM `from __future__ import annotations`: usar `Optional[X]` (SQLAlchemy compat Py3.9).
- PK SQLite-compat: `mapped_column(primary_key=True)` SEM tipo.
- `tenant_id` server_default usa `current_setting('app.tenant_id')` — conftest patcha p/ SQLite.
- Migration: revision string curta, sem guards PG p/ plain add_column.
- Tests CRUD: engine SQLite próprio (StaticPool), override `get_db`.
- Router pattern: `APIRouter(dependencies=[Depends(require_permission("compras"))])`.
- billing.py tem erros ruff UP045 pré-existentes — não tocar.
- Last migration: 0071 (add_ean_to_insumos). Next: 0072.
- Alembic path: `backend/alembic/versions/`.
- Frontend: hooks em features/<módulo>/; toast/api utils em `@/lib/`; componentes em `@/components/ui/`.
- SQLite não tem ARRAY — usar JSON para arrays no model.
- ENUM PG: usar sa.String(N) no model (SQLite-compat); migration cria TYPE no PG com guard.
- Platform router: `get_platform_db` — sem RLS, acessa todos os tenant_ids diretamente.
- Platform schemas: inline no platform_auth.py (não arquivo separado).
- `from __future__ import annotations` está em platform_repository.py — manter.
- platform_auth.py usa `Optional[X]` com `# noqa: UP045` (herdado).
- Models importados em `backend/src/models/__init__.py` para Alembic detectar.
- App-side endpoints lendo platform tables: usar `get_platform_db` para dados + `get_current_user` para auth.
- `platform_auth.py` já tem `CockpitMetricsItem` e routes de cockpit (adicionadas por issue #27).
- Cockpit queries usam PG-only SQL (DATE_TRUNC, EXTRACT, INTERVAL) — tests devem mockar o repositório.
- Patch target para mocks: `src.repositories.platform_repository.<func>` (não o import local).

## Iteration 1 - 2026-06-13T03:35:00Z (Issue #25 COMPLETE)

### Completed
- Migrations: 0074 tenant_features, 0075 assinatura_history, 0076 audit_logs
- Models: TenantFeature, AssinaturaHistory, AuditLog
- platform_repository: full tenant CRUD, assinatura update + history, user CRUD, profile permissions, feature flags upsert
- platform_auth routes: 15 new endpoints (tenants CRUD, assinatura, users, profiles, features, settings, impersonation)
- auth_service: create_access_token with optional expires_delta for 2h impersonation JWT
- check_subscription fixed to use get_db (SQLite compat in tests)
- ProfilePermission fix: pass created_at explicitly to avoid NOW() in SQLite
- 17 tests all passing
- Frontend: full hook suite in usePlatformApi.ts (create/update tenant, history, user/profile/feature CRUD, impersonation)
- PlatformTenantsPage: Nova Empresa modal + qtd_usuarios column
- PlatformTenantDetailPage: 4-tab UI (Dados/Assinatura, Usuários, Perfis, Feature Flags)
- Topbar: impersonation banner
- Commit: affbb9a

### Validation Status
- ruff: PASS | type-check: PASS | lint: PASS | build: PASS
- Tests: 17/17 new PASS; 280 total PASS; 3 pre-existing fails unrelated

### Learnings
- ProfilePermission has NOW() server_default — must pass created_at=now explicitly in SQLite tests
- check_subscription must use get_db not get_platform_db (both point to same DB in tests via override)
- Custom error handler wraps ALL HTTPException detail dicts → assert on resp.text not resp.json()["detail"]

---

## Iteration 1 - 2026-06-13T03:20:00Z (Issue #30 COMPLETE)

### Completed
- Migration 0073: platform_announcements, announcement_targets, announcement_reads
- Models: PlatformAnnouncement, AnnouncementTarget, AnnouncementRead em platform_announcements.py
- Repository: announcements_repository.py (list_with_read_counts, create, list_active_for_user, mark_read)
- Routes: /api/platform/announcements (GET + POST, platform admin auth)
- Routes: /api/app/announcements (GET ativo não lido) + /api/app/announcements/{id}/read (POST)
- main.py: rotas registradas
- 13 testes: repo (7) + API (6) — todos PASS
- Frontend: usePlatformApi.ts — AnnouncementItem + useCreateAnnouncement + usePlatformAnnouncements
- Frontend: PlatformAnnouncementsPage.tsx — tabela + modal criar (com seletor tenant specific)
- Frontend: useAnnouncements.ts — useActiveAnnouncements + useMarkAnnouncementRead
- Frontend: ComunicadoBanner em Topbar.tsx (banner dismissável, chama mark-read)
- Commit: 4850f6e

### Validation Status
- ruff: PASS | type-check: PASS | lint: PASS | build: PASS
- Tests: 13/13 novos PASS

### Learnings
- JWT payload de app user usa `user_id` (não `sub`); platform admin usa `admin_id`.
- `get_platform_db` acessível como dep em endpoint de app user → funciona em dev (mesmo DB).
- Migration 0072 já existia (platform_settings) — comunicados ficou em 0073.

---

## Iteration 1 - 2026-06-13T03:10:00Z (Issue #29 COMPLETE)

### Completed
- get_cockpit_metrics() + get_tenant_cockpit_metrics() em platform_repository.py
- GET /api/platform/cockpit + GET /api/platform/tenants/{id}/cockpit endpoints
- CockpitMetricsItem Pydantic schema inline em platform_auth.py
- usePlatformCockpit + useTenantCockpit hooks + TS interface em usePlatformApi.ts
- PlatformCockpitPage.tsx — tabela ordenável + filtro por assinatura
- 7 testes em test_platform_cockpit.py — todos PASS
- Commit: 38b2ad8

### Validation Status
- ruff: PASS | type-check: PASS | lint: PASS | build: PASS
- Tests: 7/7 novos PASS; 233 existentes PASS; 2 fail pre-existing (test_configuracoes)

---
