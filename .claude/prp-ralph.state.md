---
iteration: 1
max_iterations: 10
plan_path: "docs/issues/issues_matchpoint_v0.1.md"
started_at: "2026-05-08T00:00:00Z"
---

# Ralph Progress Log

## Codebase Patterns
- Backend uses `Optional[X]` (Python 3.9), not `X | None`
- Ruff UP035: use native `dict[x]`, `list[x]`, not `Dict`/`List` from typing
- Comanda.data_fechamento is UTC; use `_day_utc_range` + `_local_date` for SP timezone
- Compra.data_compra is plain `datetime.date` (already local, no UTC conversion needed)
- Frontend recharts has pre-existing TS errors (no @types/recharts) — do not fix those
- React Query queryKey pattern: `["dashboard", "historico", inicio, fim]`
- SQLite: `op.create_foreign_key` fails — just add column, skip FK constraint (SQLite doesn't enforce FKs anyway)
- When migration partially runs (fails mid-way), column is already created → use `alembic stamp <rev>` to advance state
- `CategoriaResponse` with recursive `children` field requires `CategoriaResponse.model_rebuild()` in Pydantic v2

## Iteration 1 - 2026-05-08T00:00:00Z

### Completed
- backend/src/repositories/dashboard_repository.py: added `historico_periodo()` and `resumo_anual()`
- backend/src/schemas/dashboard_schemas.py: added `DashboardHistoricoItem`, `DashboardResumoAnualItem`
- backend/src/services/dashboard_service.py: added `dashboard_historico()`, `dashboard_resumo_anual()`
- backend/src/api/routes/dashboard.py: added GET /historico and GET /resumo-anual routes
- frontend/src/features/dashboard/useDashboard.ts: added `useDashboardHistorico`, `useDashboardResumoAnual`
- frontend/src/features/dashboard/DashboardPage.tsx: removed Lucro Estimado, removed HeatmapMes, added tabs Resumo/Histórico with table and annual calendar grid

### Validation Status
- Ruff lint: PASS
- Backend tests: PASS (104/104)
- Frontend type-check: pre-existing recharts errors only (no new errors)
- Committed: a48f47e

---
