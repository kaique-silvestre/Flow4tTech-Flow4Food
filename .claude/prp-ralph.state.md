---
iteration: 1
max_iterations: 10
status: IN_PROGRESS
plan_path: ".claude/PRPs/plans/issue-2-get-db-concorrencia.md"
started_at: "2026-05-28T01:00:00Z"
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
- RLS policy: `USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::bigint)`
- Migration seed dialect split: PostgreSQL usa ON CONFLICT, SQLite usa INSERT OR IGNORE
- `profiles` e `system_users`: tenant_id já existia (migration 0034), FK adicionada em 0043 apenas no PG
- Alembic head após Issue 1: "0043"

## Iteration 1 - 2026-05-28

### Completed
- Migration 0042: tabela `tenants` + seed tenant_id=1 (compat com server_default="1")
- Migration 0043: tenant_id em 12 tabelas + FK em profiles/system_users + RLS + índices compostos
- Models: Tenant novo + tenant_id em Comanda, ItemComanda, Insumo, Produto, MovimentoEstoque, Compra, Pagamento, ComissaoGarcom, EventoComanda, Categoria, Fornecedor, ProfilePermission
- tests/test_rls.py: isolamento e bloqueio sem app.tenant_id (skip no SQLite)
- Commit: 10b8467

### Validation Status
- Ruff: PASS
- Mypy (src/models/): PASS (26 files)
- Tests: 61 pass / 53 fail (pre-existing) / 2 skipped (RLS, SQLite) — sem regressões

### Next Steps
- Issue 2: get_db injection + SELECT FOR UPDATE (bloqueado por Issue 1 ✓)
- Issue 3: Onboarding atômico de tenant (bloqueado por Issues 1+2)
- Issue 7: Caixa backend (bloqueado por Issue 1 ✓ — pode começar)

---
