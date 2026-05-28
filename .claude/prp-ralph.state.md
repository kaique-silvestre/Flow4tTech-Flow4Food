---
iteration: 1
max_iterations: 10
status: IN_PROGRESS
plan_path: ".claude/PRPs/plans/issue-1-rls-foundation.md"
started_at: "2026-05-28T00:00:00Z"
---

# Ralph Progress Log

## Codebase Patterns
- Backend usa `Optional[X]` não `X | None` (SQLAlchemy mapper quebra no Python 3.9)
- Ruff UP035: usar `dict[x]`, `list[x]` nativos, não `Dict`/`List` do typing
- Migration revision IDs devem ser strings curtas (<=32 chars)
- bcrypt direto (`import bcrypt`), não via passlib
- `get_settings()` via `lru_cache` — monkeypatch DEVE ser em `src.services.auth_service.get_settings`
- `require_permission` em `src/api/dependencies.py`
- pyjwt 2.13.0: `import jwt` / `from jwt.exceptions import InvalidTokenError`
- JWT_SECRET mínimo 32 chars; test: `"test-secret-only-for-tests-32chars!!"`
- Tests usam SQLite in-memory; RLS é PostgreSQL-only → usar skip guard nos testes
- `op.get_bind().dialect.name == 'postgresql'` para guards em migration
- Alembic migration head atual: "0041"
- `profiles` e `system_users` já têm `tenant_id` com server_default="1" (migration 0034)
- `profile_permissions` NÃO tem tenant_id ainda
- Unique index no email do system_users: já permite múltiplos NULLs no PostgreSQL (NULL != NULL)
