# CI/CD — Pipeline de Integração e Deploy

## Visão Geral

```
PR aberto → CI roda (lint + types + migrations + tests)
                ↓ passa
          merge em staging → Railway deploya staging automaticamente
                ↓ validado manualmente
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
| Migration check | `alembic check` | Sem migrations pendentes não commitadas |
| Testes | `pytest` | Testes unitários e de integração |

O banco de testes é um PostgreSQL 16 efêmero criado pelo próprio CI (Docker service). Não toca nenhum banco real.

### O que roda no frontend

| Etapa | Ferramenta | O que verifica |
|---|---|---|
| Lint | `eslint src/` | Erros de código, hooks mal usados, `--max-warnings 0` |
| Types | `tsc --noEmit` | Tipos TypeScript incorretos |
| Build | `vite build` | Garante que o bundle compila sem erro |
| Testes | `vitest run` | Testes de componente |

### Regra de merge

- PR para `staging` ou `main`: **CI deve passar** antes do merge
- Testes estão com `continue-on-error: true` temporariamente enquanto não há testes escritos — remover quando os primeiros testes forem criados

## Deploy — Staging

Automático após merge em `staging`:

1. Railway detecta push
2. Build via Nixpacks
3. Startup: `alembic upgrade head && uvicorn src.main:app ...`
4. Health check em `/health`

Se o deploy falhar, o Railway mantém a versão anterior rodando.

## Deploy — Produção

**Manual e deliberado.** Nunca automático para migrations.

### Passo a passo

```bash
# 1. Merge staging → main
git checkout main
git merge staging
git push origin main
# Railway deploya código automaticamente

# 2. Verificar que o deploy foi SUCCESS no dashboard

# 3. Se houver migration: abrir Console Railway (production)
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
alembic check             # sem pendentes
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

## Próximos passos — o que falta para CI ser 100% eficaz

### Prioridade Alta

1. **Escrever testes de integração no backend** — sem testes, CI passa mas não valida lógica de negócio. Foco inicial:
   - Autenticação (login, refresh, logout)
   - RLS: garantir que tenant A não vê dados do tenant B
   - CRUD das entidades principais (comandas, produtos, insumos)

2. **Escrever testes de componente no frontend** — foco em:
   - Fluxo de login
   - Renderização das páginas principais

### Prioridade Média

3. **Branch protection rules no GitHub:**
   - `main` e `staging`: require PR, require CI passing, no direct push
   - Configurar em: Settings → Branches → Branch protection rules

4. **Deploy preview do frontend (Vercel):**
   - Branch `staging` com `VITE_API_URL` apontando para backend staging
   - Permite testar frontend + backend staging juntos antes de ir pra prod

### Prioridade Baixa

5. **Notificação de falha de CI** — Slack/email quando CI falha em `staging`
6. **Análise de segurança** — `bandit` no backend (SAST), `npm audit` no frontend
