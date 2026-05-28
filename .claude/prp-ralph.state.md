---
iteration: 2
max_iterations: 10
status: COMPLETE
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
- `get_tenant_db` guard: `get_settings().DATABASE_URL.startswith("postgresql")`
- `SET LOCAL app.tenant_id` (não `SET`) — escopo de transação, não vaza no pool
- `get_tenant_db` depende de `get_db` + `get_current_user` — FastAPI faz cache dentro do request
- Substituir `get_db` em rotas: remover `get_current_user` e `get_db` e usar só `get_tenant_db`
- Tests de rotas: sempre override BOTH `get_db` AND `get_current_user`
- `_next_numero_dia` usava `::date` (PostgreSQL-only) → fix: usar `cast(Comanda.created_at, Date)`
- Decimal precision: SQLite retorna mais casas decimais que PostgreSQL — usar `Decimal(x) == Decimal(y)`
- `TENANT_ID = 1` removido de users_service, profiles_service, auth_service
- services agora recebem `tenant_id: int` como parâmetro explícito
- routes extraem `payload["tenant_id"]` e passam para services
- Alembic head após Issue 2: "0043" (não muda — Issue 2 sem novas migrations)

## Iteration 1 - 2026-05-28

### Completed (Issue 1)
- Migration 0042: tabela `tenants` + seed tenant_id=1
- Migration 0043: tenant_id + RLS + índices compostos em 14 tabelas
- Models: Tenant + tenant_id em todos os modelos operacionais
- tests/test_rls.py (skip SQLite)
- Commit: 10b8467

### Validation Status
- Ruff: PASS
- Mypy (src/models/): PASS
- Tests: 61 pass / 53 fail (pre-existing) / 2 skipped

## Iteration 2 - 2026-05-28

### Completed (Issue 2)
- `get_tenant_db` em dependencies.py: SET LOCAL app.tenant_id do JWT (PG-only guard)
- Todas as rotas operacionais migradas de `get_db` → `get_tenant_db`
- `estoque_repository.get_insumo_for_update`: adicionado `.with_for_update()`
- `_reservar_estoque` e `_dar_baixa_estoque`: usam `get_insumo_for_update`
- `AplicarDescontoRequest`: campo `version: int` adicionado
- `CancelarComandaRequest`: nova schema com `version: int`
- `aplicar_desconto`: CAS via `increment_version` → 409 se stale
- `cancelar_comanda`: aceita `data: CancelarComandaRequest`, CAS → 409 se stale
- `users_service`: TENANT_ID removido, `tenant_id: int` como parâmetro
- `profiles_service`: TENANT_ID removido, `tenant_id: int` como parâmetro
- `auth_service`: TENANT_ID → `_DEFAULT_TENANT_ID` (TODO Issue 3)
- `users.py` e `profiles.py` routes: extraem tenant_id do payload JWT
- `_next_numero_dia`: fix SQLite compat com `cast(Comanda.created_at, Date)`
- tests/test_issue2_cas.py: 4 testes CAS ✓
- tests/test_issue2_concorrencia.py: skip em SQLite, roda em PostgreSQL
- Commit: da5dad3

### Validation Status
- Ruff: PASS
- Mypy (arquivos modificados): PASS (7 erros pre-existentes em dashboard/metodos)
- Tests: 78 pass / 52 fail (pre-existing) / 3 skipped — +17 novos passes

### Next Steps
- Issue 3: Onboarding atômico de tenant (bloqueado por Issues 1+2 ✓)
- Issue 7: Caixa backend (bloqueado por Issue 1 ✓)
- Issue 8: Rebranding (independente)

---
