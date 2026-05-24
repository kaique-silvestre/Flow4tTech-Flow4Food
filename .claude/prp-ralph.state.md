---
iteration: 3
max_iterations: 10
plan_path: "docs/issues/issues_jwt_auth_profissionalizacao.md"
started_at: "2026-05-24T00:00:00Z"
---

# Ralph Progress Log

## Codebase Patterns
- Backend uses `Optional[X]` (Python 3.9), not `X | None` (str|None quebra SQLAlchemy mapper)
- Ruff UP035: use native `dict[x]`, `list[x]`, not `Dict`/`List` from typing
- Migration revision IDs devem ser strings curtas (<=32 chars)
- bcrypt usado direto (`import bcrypt`), não via passlib
- `get_settings()` via `lru_cache` — monkeypatch DEVE ser em `src.services.auth_service.get_settings`, não em `src.core.config.get_settings`
- `require_permission` em `src/api/dependencies.py`
- `create_access_token` em `src/services/auth_service.py`
- Tests fake_user precisa de: `{"sub": "1", "user_id": 1, "tenant_id": 1, "permissions": [...]}`
- pyjwt 2.13.0 instalado; `import jwt` / `from jwt.exceptions import InvalidTokenError`
- JWT_SECRET mínimo 32 chars (config.py min_length=32)
- Test JWT_SECRET: `"test-secret-only-for-tests-32chars!!"`

## Iteration 1 - 2026-05-24

### Completed
- Issue 1: 4 correções de auth (bypass, expiração, secret min-length, migração pyjwt)
- Fix pre-existente profiles.py (str|None → Optional[str] + noqa UP045)
- Fix pre-existente compras_service.py SIM108
- Todos os tests de auth (6/6 passando)
- Commit: f12c5cd

### Validation Status
- Ruff: PASS (src/ limpo)
- Mypy (arquivos modificados): PASS
- Tests auth: PASS (6/6)
- Tests totais: 55 pass / 53 fail (falhos são pre-existentes: campo "pessoas" na API de comandas)

### Next Steps
- Issue 2: logout com blacklist Postgres
  - Campo `jti` (uuid4) no payload do token
  - Tabela `revoked_tokens` via migration Alembic
  - Repositório com revoke/is_revoked/delete_expired
  - Verificação em get_current_user
  - Endpoint /logout efetivo (204)
  - Job APScheduler para limpeza horária

---
