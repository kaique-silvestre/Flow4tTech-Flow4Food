---
iteration: 1
max_iterations: 10
plan_path: ".claude/PRPs/plans/issue-11-relatorios-financeiros.md"
started_at: "2026-05-08T00:00:00Z"
---

# Ralph Progress Log

## Codebase Patterns
- Backend: FastAPI + SQLAlchemy + Pydantic. Python 3.9 → `Optional[X]` not `X | None`.
- All routes use `get_db` + `get_current_user` deps. Router registered in `main.py`.
- Tests use `client`, `db`, `auth_headers` fixtures from conftest. `_fechar_comanda_simples` helper pattern used in test_relatorios.py.
- Frontend: React + TanStack Query. Hooks in `useRelatorios.ts`, pages in `features/relatorios/`. Routes added to `App.tsx`.
- `formatCurrency` from `@/lib/format`. `date-fns` available for date formatting.
- `useGarcons` hook exists at `features/cadastros/garcons/useGarcons.ts`.
- Cortesia items: `preco_unitario=0` in DB. JOIN to `Item.preco_venda` to get lost revenue.
- `faturamento_bruto` in DRE = `sum(comanda.total + desconto_valor)` (pre-discount gross, cortesias excluded because preco=0).
- Lint runs: `ruff check .` in backend. `npm run lint` in frontend.
