# CI/CD — Pipeline de Integração e Deploy

## Visão Geral

```
PR aberto → CI roda (lint + types + migrations + tests)
                ↓ passa
          merge em staging → Railway deploya staging automaticamente
                ↓ smoke test confirma /health
          validação manual (ver staging-checklist.md)
                ↓ aprovado
          merge em main → Railway deploya prod (sem migration)
                ↓ deliberadamente
          migration manual no Console Railway
```

## GitHub Actions — `.github/workflows/ci.yml`

O pipeline roda em todo **pull request** para `staging` ou `main`, e em todo **push** direto para `staging`.

### O que roda no backend

| Etapa | Ferramenta | O que verifica |
|---|---|---|
| Lint | `ruff check src/` | Erros de código, imports não usados, style |
| Types | `mypy src/` | Tipos incorretos, `None` não tratados |
| Migration heads | `alembic heads` | Garante que só existe 1 head (sem branch de migration) |
| Migration test | `alembic upgrade head` | Migration roda do zero sem erro |
| Testes | `pytest` | Testes unitários e de integração |

> **Nota:** `alembic check` (paridade estrita model↔migration) está desabilitado. As migrations de tenant-isolation adicionaram ~144 indexes/type changes que os ORM models não declaram. Reativar após os models espelharem o schema completo.

O banco de testes é um PostgreSQL 16 efêmero criado pelo próprio CI (Docker service). Não toca nenhum banco real.

### O que roda no frontend

| Etapa | Ferramenta | O que verifica |
|---|---|---|
| Lint | `eslint src/` | Erros de código, hooks mal usados, `--max-warnings 0` |
| Types | `tsc --noEmit` | Tipos TypeScript incorretos |
| Build | `vite build` | Garante que o bundle compila sem erro |
| Testes | `vitest run` | Testes de componente |

> **Nota:** `npm test` roda com `continue-on-error: true` enquanto não há testes escritos. Remover essa flag quando os primeiros testes forem criados.

### Regra de merge

- PR para `staging` ou `main`: **CI deve passar** antes do merge
- Branch protection ativa em ambas — push direto bloqueado

## Smoke Test — `.github/workflows/smoke-test.yml`

Roda **após push em `staging`** (ou seja, após merge de PR). Aguarda o Railway terminar o deploy e confirma que o backend está respondendo.

O que verifica:
- `GET /health` retorna `200` no backend staging
- Faz polling com retry (até 10 tentativas, 30s de intervalo = ~5 min máximo)

Se o smoke test falha, significa que o deploy do Railway crashou. Investigar logs no Railway dashboard antes de abrir PR para `main`.

## Deploy — Staging

Automático após merge em `staging`:

1. Railway detecta push
2. Build via Nixpacks
3. Startup: `alembic upgrade head && uvicorn src.main:app ...`
4. Health check em `/health`
5. Smoke test do GitHub Actions confirma resposta

Se o deploy falhar, o Railway mantém a versão anterior rodando.

## Deploy — Produção

**Manual e deliberado.** Nunca automático para migrations.

### Passo a passo

```bash
# 1. Validar staging (ver staging-checklist.md)

# 2. Merge staging → main
git checkout main
git merge staging
git push origin main
# Railway deploya código automaticamente

# 3. Verificar que o deploy foi SUCCESS no dashboard

# 4. Se houver migration: abrir Console Railway (production)
/opt/venv/bin/alembic current   # confirmar revision atual
/opt/venv/bin/alembic upgrade head
/opt/venv/bin/alembic current   # confirmar que subiu
```

## Rodando CI localmente antes de abrir PR

### Backend

```powershell
cd backend
.venv\Scripts\Activate.ps1

ruff check src/           # lint
mypy src/                 # types
alembic heads             # deve retornar 1 linha
pytest --tb=short -q      # testes
```

### Frontend

```powershell
cd frontend
npm run lint              # eslint
npm run type-check        # tsc
npm run build             # build completo
npm test                  # vitest
```

## Status das pendências

| Item | Status |
|---|---|
| CI pipeline (lint, types, build, migrations) | ✅ Operacional |
| Branch protection `staging` e `main` | ✅ Ativo — PR + CI obrigatórios |
| Smoke test pós-deploy staging | ✅ Implementado (`smoke-test.yml`) |
| Testes de integração backend | ⏳ Pendente — ver seção abaixo |
| Testes de componente frontend | ⏳ Pendente — ver seção abaixo |
| Frontend staging com URL própria (Vercel) | ⏳ Pendente — ver `workflow-3-ambientes.md` seção 10.3 |

## Próximos passos — Testes automatizados

### Prioridade Alta — Backend

Sem testes, CI passa mas não valida lógica de negócio. Foco inicial:

1. **Autenticação** — login, refresh, logout
2. **RLS** — tenant A não vê dados do tenant B (crítico para segurança)
3. **CRUD das entidades principais** — comandas, produtos, insumos, consumo interno

Estrutura sugerida:
```
backend/tests/
  conftest.py           # fixtures: db, client, auth headers por tenant
  test_auth.py
  test_rls.py           # cria 2 tenants, verifica isolamento
  test_comandas.py
  test_produtos.py
  test_consumo_interno.py
```

### Prioridade Média — Frontend

Foco em:
- Fluxo de login (renderiza, submete, redireciona)
- Páginas principais não crasham ao renderizar
