---
iteration: 1
max_iterations: 10
plan_path: ".claude/PRPs/plans/issue-2-auth.md"
started_at: "2026-05-07T00:00:00Z"
---

# Ralph Progress Log

## Codebase Patterns
- Backend usa `uv run` para rodar comandos Python (pyproject.toml com uv)
- Estrutura Deep Models: models → repositories → services → api/routes
- Exception handler global em `src/core/errors.py` — usar `AppError(ErrorCode.X, msg, http_status=N)`
- `ErrorCode.SENHA_INCORRETA` já definido em errors.py
- Settings via `get_settings()` (lru_cache) — importar de `src.core.config`
- Frontend usa `npm` (não pnpm/bun)
- Sonner toast: `toast.error()` persistente, `toast.success()` 2-3s
- Axios instance em `src/lib/api.ts` com baseURL via `VITE_API_URL`
- Auth store: Zustand com `persist` middleware → localStorage
- `src/core/errors.py` já tem `ErrorCode.SENHA_INCORRETA` e `ErrorCode.UNAUTHORIZED`
