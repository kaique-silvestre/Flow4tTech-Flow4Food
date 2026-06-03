# Pendências — Kaique

Ações que exigem acesso de owner (GitHub, Railway, Vercel). Pedro não consegue executar.

---

## 1. Branch Protection — GitHub

**Repo:** `kaique-silvestre/Flow4tTech-Flow4Food`

Settings → Branches → Add branch protection rule

Criar regra para **`main`** e repetir para **`staging`**:

| Configuração | Valor |
|---|---|
| Branch name pattern | `main` (depois `staging`) |
| Require pull request before merging | ✅ |
| Required approving reviews | 1 |
| Dismiss stale reviews when new commits pushed | ✅ |
| Require status checks to pass | ✅ |
| Status checks obrigatórios | `backend` e `frontend` |
| Require branches to be up to date before merging | ✅ |
| Do not allow bypassing the above settings | ✅ |

> Os checks `backend` e `frontend` só aparecem no dropdown após o CI rodar ao menos uma vez no branch. Pedro vai abrir o PR e rodar o CI — depois disso você configura.

---

## 2. Backup Automático do PostgreSQL — Railway

**Projeto:** `delightful-passion` (Railway)

O plano atual não exibe opção de backup automático. Duas opções:

**Opção A — Upgrade de plano (recomendado)**
Railway Dashboard → Settings → Billing → Upgrade to Pro.
Backups diários ficam disponíveis no serviço Postgres.

**Opção B — Sem upgrade**
Avisar Pedro para implementar script de `pg_dump` agendado via GitHub Actions.

---

## 3. Frontend Staging — Vercel

**Projeto:** frontend do sistema no Vercel (conta Kaique)

1. Settings → Git → conectar branch `staging`
2. Settings → Environment Variables → adicionar:
   - Environment: Preview
   - Key: `VITE_API_URL`
   - Value: URL do backend staging no Railway
     (Railway Dashboard → projeto → environment `staging` → serviço `Flow4Tech-Flow4Food` → Settings → Domains)
3. Fazer um push em `staging` para triggerar o deploy

---

## 4. Aplicar Migration 0050 em Produção

Depois que o PR `development → staging → main` for mergeado e o deploy de prod estiver `SUCCESS`:

Railway Console → environment `production`:
```bash
/opt/venv/bin/alembic current
/opt/venv/bin/alembic upgrade head
/opt/venv/bin/alembic current  # confirmar que está em 0050
```

> **Crítico:** sem esta migration, todo request autenticado falha em prod (`app_user` role inexistente).
