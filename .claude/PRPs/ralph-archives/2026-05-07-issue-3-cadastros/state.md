---
iteration: 1
max_iterations: 10
plan_path: ".claude/PRPs/plans/issue-3-cadastros.md"
started_at: "2026-05-07T14:00:00Z"
---

# Ralph Progress Log

## Codebase Patterns
- Backend usa `.venv/bin/` para rodar comandos Python (uv não disponível no PATH do shell)
- Estrutura Deep Models: models → repositories → services → api/routes (pure functions)
- `AppError(ErrorCode.X, msg, http_status=N)` para erros — importar de `src.core.errors`
- `ErrorCode.NOT_FOUND`, `UNAUTHORIZED` já existem em errors.py
- Settings via `get_settings()` (lru_cache) — `from src.core.config import get_settings`
- SQLAlchemy 2.0: `Mapped[Type]`, `mapped_column()`, `select()` syntax
- Python 3.9: usar `Optional[X]` não `X | None`
- Pydantic response schemas precisam de `model_config = ConfigDict(from_attributes=True)`
- Frontend usa `npm` (não pnpm/bun)
- Axios instance em `src/lib/api.ts`, auth store Zustand em `src/stores/authStore.ts`
- Sonner toast: `toast.error()` persistente, `toast.success()` 2-3s
- Importar UI de `@/components/ui/*` (button, dialog, input, label existem)
- react-hook-form + zodResolver pattern (ver features/auth/LoginPage.tsx)
- TanStack Query: useQuery + useMutation, invalidateQueries on success
- **bcrypt 5.0.0 incompatível com passlib** — N/A neste issue (sem hashing)
- Alembic migration pattern: `down_revision`, `upgrade()` com `op.create_table()`, seed via `op.execute()`
- Test fixtures em `tests/conftest.py` — usar `auth_client` para requests autenticadas
