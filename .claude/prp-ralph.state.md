---
iteration: 1
max_iterations: 8
plan_path: ".claude/PRPs/plans/issue-20-importacao-nfe.md"
started_at: "2026-06-11T18:00:00Z"
status: IN_PROGRESS
---

# Ralph Progress Log

## Codebase Patterns
- Models SEM `from __future__ import annotations`: usar `Optional[X]` (SQLAlchemy compat Py3.9).
- PK SQLite-compat: `mapped_column(primary_key=True)` SEM tipo.
- `tenant_id` server_default usa `current_setting('app.tenant_id')` — conftest patcha p/ SQLite `DefaultClause(sa.text("1"))`.
- Migration: revision string curta, sem guards PG p/ plain add_column (funciona em ambos).
- Tests CRUD: engine SQLite próprio (StaticPool), override `get_db` (não `get_tenant_db` — o override de get_db cobre).
- Router pattern: `APIRouter(dependencies=[Depends(require_permission("compras"))])`.
- billing.py tem erros ruff UP045 pré-existentes — não tocar.
- Last migration: 0069 (merge_estabelecimento_into_tenants).
- Alembic path: `backend/alembic/versions/`.
- Frontend: hooks em features/<módulo>/; toast/api utils em `@/lib/`; componentes em `@/components/ui/`.
- SQLite não tem ARRAY — usar JSON para arrays no model.
- ENUM PG: usar sa.String(N) no model (SQLite-compat); migration cria TYPE no PG com guard.
- Rota `/importar-nfe` DEVE ser registrada ANTES de `/{compra_id}` (FastAPI resolve em ordem).

---
