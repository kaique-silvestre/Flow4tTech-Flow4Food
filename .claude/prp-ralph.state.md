---
iteration: 1
max_iterations: 10
plan_path: ".claude/PRPs/plans/issue-12-dashboard.md"
started_at: "2026-05-08T12:00:00Z"
---

# Ralph Progress Log

## Codebase Patterns
- Backend: FastAPI + SQLAlchemy + Pydantic. Python 3.9 → `Optional[X]` not `X | None`.
- All routes use `get_db` + `get_current_user` deps. Router registered in `main.py`.
- Tests: engine SQLite em memória, fixture `c` (TestClient), helpers inline. `_set_custo_medio` via direct DB update.
- Frontend: React + TanStack Query. `formatCurrency` from `@/lib/format`. `api` from `@/lib/api`.
- `_day_utc_range` em relatorio_repository.py — reusar no dashboard_repository.
- Bucketing de hora feito em Python (não SQL) para evitar dependência de timezone do banco.
- Recharts não instalado — instalar com `npm install recharts` antes de criar componentes.
- Lint runs: `ruff check .` in backend. `npm run lint` in frontend.

---
