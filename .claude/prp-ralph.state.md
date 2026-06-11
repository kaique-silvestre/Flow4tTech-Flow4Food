---
iteration: 1
max_iterations: 10
plan_path: ".claude/PRPs/plans/issue-16-painel-admin-tenants.md"
started_at: "2026-06-11T04:00:00Z"
---

# Ralph Progress Log

## Codebase Patterns
- Models SEM `from __future__ import annotations`: usar `Optional[X]` (SQLAlchemy compat Py3.9).
- PK SQLite-compat: `mapped_column(primary_key=True)` SEM tipo (não `sa.BigInteger()`).
- `created_at`/`server_default NOW()` falha no SQLite — passar valor explícito em fixtures.
- tenant_id RLS server_default; conftest patcha p/ SQLite (`DefaultClause(sa.text("1"))`).
- Migration: revision string curta, guards PG-only com `op.get_bind().dialect.name == 'postgresql'`.
- Tests CRUD: engine SQLite próprio (StaticPool), override BOTH `get_db` + `get_platform_db`.
- Router pattern: `APIRouter(dependencies=[Depends(require_permission("screen"))])`.
- billing.py tem erros ruff UP045 pré-existentes — não tocar.
- Last migration: 0058 (tenant_eventos).
- Frontend: hooks em `@/lib/api`; toast em `@/lib/toast`; componentes em `@/components/ui/`.
- App.tsx routing pattern: need to check before adding route.
- Segunda instância de TestClient p/ mesmo app causa ConflictingIdError no scheduler — usar um único client e testar tenant_id diretamente na DB.
- navConfig.ts: adicionar ícone no import + item em NAV_ITEMS.
- SQLite não tem ARRAY — usar JSON para dias_semana/dias_mes no model (sa.JSON()); migration cria INT[] no PG via ARRAY(Integer).
- ENUM PG: usar sa.String(10) no model (SQLite-compat); migration cria o TYPE no PG com guard.
- `dias_semana`/`dias_mes` devem ser `None` (não `[]`) para recorrencia='nenhuma' no payload — backend valida.
- PromoçaoResponse.produto_ids preenchido manualmente no service via _get_produto_ids (não mapeado no ORM).
- Platform tests: override get_db + get_platform_db com mesma sessão SQLite; seed Tenant/Assinatura com created_at/updated_at explícitos.
- `platform_auth.router` já tem `Depends(require_platform_admin)` — novos endpoints do painel vão nesse router.
- Tenant.created_at / Assinatura.created_at+updated_at precisam de valor explícito em fixtures SQLite.

