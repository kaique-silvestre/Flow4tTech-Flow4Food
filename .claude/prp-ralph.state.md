---
iteration: 8
max_iterations: 10
status: COMPLETE
plan_path: "docs/issues/issues_v1_lancamento_comercial.md"
started_at: "2026-05-28T00:00:00Z"
---

# Ralph Progress Log

## Codebase Patterns
- Models com `from __future__ import annotations`: usar `X | None` (ruff UP045 exige)
- Models SEM `from __future__ import annotations`: usar `Optional[X]` para SQLAlchemy compat
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

## Iteration 3 - 2026-05-28

### Completed (Issue 7)
- Migration 0044: caixa_sessoes + caixa_movimentos com tenant_id, RLS, índice parcial único (uma sessão aberta por tenant, PG-only)
- Models: CaixaSessao, CaixaMovimento em src/models/caixa.py
- caixa_repository: get_sessao_aberta, criar_sessao, fechar_sessao, criar_movimento, list_movimentos, sum_movimentos_tipo, sum_pagamentos_dinheiro
- caixa_service: abrir_caixa (409 se duplicado), fechar_caixa (valor_esperado = abertura + dinheiro + suprimentos - sangrias), registrar_movimento, get_sessao_aberta
- api/routes/caixa.py: POST /api/caixa/abrir, POST /api/caixa/fechar, POST /api/caixa/movimentos, GET /api/caixa/sessao
- require_permission("caixa") em todos os endpoints
- 12 testes: fluxo completo, 409 dupla abertura, 404 sem sessão, 403 sem permissão
- Commit: 1ec096a

### Validation Status
- Ruff: PASS
- Mypy (5 arquivos caixa): PASS
- Tests: 12/12 caixa PASS; 78 pass / 52 fail (pre-existing) / 3 skipped — sem regressões

### Next Steps
- Issue 3: Onboarding atômico de tenant (bloqueado por Issues 1+2 ✓)
- Issue 9: Frontend tela de caixa (bloqueado por Issue 7 ✓)

## Iteration 5 - 2026-05-28

### Completed (Issue 3)
- Migration 0045: tabela assinaturas (status trial/ativa/vencida/cancelada/suspensa, FK tenant_id UNIQUE)
- Model: Assinatura (id sem BigInteger para SQLite compat)
- Tenant model: BigInteger removido do id.pk para SQLite compat (PG usa sequence na migration)
- tenant_repository: create, get_by_id, update, list, get_assinatura_by_tenant, create_assinatura, clone_profiles_from_seed
- tenant_service: criar_tenant (transação única, rollback automático), get_tenant, update_existing_tenant, get_all_tenants
- schemas/tenants.py: TenantCreate, TenantUpdate, TenantResponse, AssinaturaInfo
- api/routes/admin.py: POST/GET/PATCH /api/admin/tenants + require_superadmin (SUPERADMIN_TOKEN env var)
- config.py: SUPERADMIN_TOKEN field adicionado
- main.py: admin router registrado em /api/admin
- 14 testes: 14/14 PASS — auth guard, criação, rollback atômico, GET, PATCH
- Commit: a534191

### Codebase Patterns (novos)
- Modelos SQLite-compat: NUNCA usar `sa.BigInteger()` na coluna pk — usar `mapped_column(primary_key=True)` sem tipo
- `server_default=sa.text("NOW()")` falha no SQLite se inserir sem o campo — passar `created_at=now` explícito nas fixtures/services
- Superadmin auth: SUPERADMIN_TOKEN env var, `Authorization: Bearer <token>`, monkeypatch DEVE limpar cache `get_settings.cache_clear()`
- `pydantic[email]` (email-validator) precisa ser instalado separado para usar `EmailStr`

### Validation Status
- Ruff: PASS
- Tests: 92 pass (78 anteriores + 14 novos) / 52 fail (pré-existentes) / sem regressões

### Next Steps
- Issue 4: JWT multi-tenant (bloqueado por Issues 1+3 ✓)
- Issue 5: Sistema de assinaturas (depende de Issues 3+4)

---

## Iteration 4 - 2026-05-28

### Completed (Issue 9)
- useCaixa.ts: useSessaoAberta (404→null), useAbrirCaixa, useFecharCaixa, useRegistrarMovimento
- CaixaPage.tsx: 3 fluxos — AberturaCaixa, TurnoAtivo (mov inline), FechamentoCaixa + ResultadoFechamento
- Sobra/quebra com cor distinta (verde/vermelho)
- App.tsx: rota /caixa com RequirePermission screen="caixa"
- Sidebar.tsx: item Caixa (Banknote icon) com screen="caixa"
- Commit: b08d277

### Validation Status
- Type-check: PASS
- Lint (new files): PASS (2 erros pre-existentes em RedefinirSenhaPage + ComandaAbertaPage)
- Build: PASS (8.77s)

### Next Steps
- Issue 4: JWT multi-tenant
- Issue 5: Sistema de assinaturas
- Issue 6: SubscriptionGuard frontend

---

## Iteration 6-8 - 2026-05-28

### Completed (Issues 4, 5, 6)

**Issue 4 — JWT multi-tenant:**
- config.py: JWT_EXPIRES_HOURS → JWT_EXPIRES_MINUTES = 15
- auth_service.py: removed _DEFAULT_TENANT_ID, added subscription_status to JWT payload
- _build_token_response: accepts subscription_status param
- rotate_refresh_token: re-reads assinatura from DB on refresh
- login: uses get_user_by_username_global (cross-tenant, no hardcoded tenant_id)
- users_repository.py: added get_user_by_username_global
- Tests: 5 new tests, all pass (commit 552ea09)

**Issue 5 — Billing system:**
- Migration 0046: planos + pagamentos_assinatura tables
- models/billing.py: Plano, PagamentoAssinatura (Python-level defaults for SQLite compat)
- repositories/billing_repository.py: CRUD for plans, payments, subscription state, marcar_vencidas (ORM-based for SQLite compat)
- services/billing_service.py: listar_planos, criar_plano, registrar_pagamento, atualizar_assinatura, marcar_assinaturas_vencidas
- schemas/billing.py: PlanoCreate, PlanoInfo, PagamentoCreate, PagamentoInfo, AssinaturaUpdate
- api/routes/admin.py: 5 new endpoints (plans CRUD, payments, subscription PATCH)
- api/dependencies.py: require_active_subscription → 402 if not {ativa, trial}
- core/scheduler.py: daily job _marcar_assinaturas_vencidas at 00:30
- Tests: 8 new tests (commit 11ed3e9)

**Issue 6 — Frontend SubscriptionGuard:**
- authStore.ts: added subscription_status? to AuthUser interface
- api.ts: 402 interceptor → Admin to /assinatura-vencida, others to /conta-suspensa
- AssinaturaVencidaPage.tsx: Admin billing info + Flow4Tech contact
- ContaSuspensaPage.tsx: simple "Conta suspensa — procure o responsável"
- App.tsx: routes /assinatura-vencida and /conta-suspensa inside RequireAuth
- Fixed authStore.ts filename casing (authstore → authStore via 2-step rename)
- Type-check: PASS, Build: PASS (commit eee1994)

### Validation Status
- Ruff: PASS (all backend files)
- Backend tests: 105 pass / 52 pre-existing fail / 3 skip
- Frontend type-check: PASS
- Frontend build: PASS (9.46s)
- Lint: 2 pre-existing errors in RedefinirSenhaPage + ComandaAbertaPage (not new)

### New Codebase Patterns
- Models with `from __future__ import annotations`: use `X | None` (ruff UP045)
- SQLite compat: use Python-level `default=lambda: datetime.now(...)` not just `server_default=sa.text("NOW()")`
- marcar_vencidas: use SQLAlchemy ORM query (not raw SQL with NOW()) for SQLite compat
- authStore.ts casing: file must be `authStore.ts` (capital S) — Windows filesystem case-insensitive but TypeScript isn't

---
