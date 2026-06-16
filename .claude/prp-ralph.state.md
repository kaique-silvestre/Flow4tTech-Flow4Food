---
iteration: 1
max_iterations: 6
plan_path: ".claude/PRPs/plans/issue-36-audit-logs.md"
started_at: "2026-06-16T02:00:00Z"
status: COMPLETE
---

# Ralph Progress Log

## Iteration 1 — 2026-06-16T02:00:00Z (Issue #36 COMPLETE)

### Completed
- Backend: audit_service.py — log() + log_background() (fire-and-forget via BackgroundTasks)
- Backend: platform_audit.py — GET /api/platform/audit-logs com filtros + paginação
- Backend: main.py — router registrado em /api/platform
- Backend: users.py — create/update/delete instrumentados com BackgroundTasks
- Backend: platform_auth.py — create_tenant, update_assinatura, update_assinatura_full, impersonate_user instrumentados
- Backend: users_service.py — passa created_at/updated_at explícito (SQLite compat fix)
- Tests: 5 testes (impersonation→audit, filtros, paginação) — 301/304 PASS
- Frontend: usePlatformApi.ts — useAuditLogs hook + tipos
- Frontend: PlatformAuditPage.tsx — tabela completa + filtros + paginação
- Issue #36 closed, commit: d551400

### Validation Status
- type-check: PASS | lint: PASS | build: PASS
- Tests: 301 PASS (3 pre-existing failures: test_comprovante, test_configuracoes x2)

### Learnings
- log_background() deve silenciar exceções (fire-and-forget) — evita quebrar outros tests que usam PlatformSessionLocal diferente
- users_service.create_new_user não passava created_at/updated_at — corrigido (SQLite compat, mesmo padrão do platform_repository)
- create_tenant em platform_auth.py não tinha require_platform_admin — adicionado ao instrumentar

---

## Iteration 1 - 2026-06-14T03:00:00Z (Issue #34 COMPLETE)

### Completed
- `require_feature(key)` dependency: no row = enabled; explicit `enabled=False` → 403
- `GET /api/app/features` at `/api/app/features`
- `require_feature` on 14+ route files (all modules)
- `useFeatureFlags` hook (react-query, 5min stale)
- Sidebar: filters by feature flag + permission
- navConfig: `feature?` field on all nav items
- PlatformTenantDetailPage: 11 modules, PT-BR labels, tab → "Módulos"
- 8 tests PASS; 293 total PASS; 3 pre-existing fails only
- Commit: 159caf5

### Validation Status
- ruff: PASS (4 pre-existing in billing.py/cockpit_service.py)
- type-check: PASS | lint: PASS | build: PASS
- Tests: 8/8 new PASS

### Learnings
- `Assinatura` model: pass `data_inicio=now, updated_at=now` explicitly in SQLite tests
- `db.flush()` + read `t.id` before `db.close()` — not `db.refresh(t)` after close
- Python 3.9: no `list | None` syntax — use `list = None`
- insumos.py permission = "estoque" but feature = "cadastros" (nav group)
- contas_pagar.py permission = "compras" but feature = "financeiro" (nav group)

---

## Codebase Patterns
- Models SEM `from __future__ import annotations`: usar `Optional[X]` (SQLAlchemy compat Py3.9).
- PK SQLite-compat: `mapped_column(primary_key=True)` SEM tipo.
- Tests CRUD: engine SQLite próprio (StaticPool), override `get_db`.
- Router pattern: `APIRouter(dependencies=[Depends(require_permission("X"))])`.
- billing.py tem erros ruff UP045 pré-existentes — não tocar.
- `require_feature` default: NO ROW = feature enabled (only explicit enabled=False blocks).
- JWT payload de app user usa `user_id`; platform admin usa `admin_id`.
- Custom error handler wraps ALL HTTPException detail dicts → assert on resp.text.
- check_subscription must use get_db not get_platform_db.
- `Assinatura` model: pass `data_inicio=now, updated_at=now` explicitly in SQLite tests.
- Python 3.9: use `Optional[X]` or `X = None` for params, not `X | None`.
