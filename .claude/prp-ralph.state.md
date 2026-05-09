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

---
