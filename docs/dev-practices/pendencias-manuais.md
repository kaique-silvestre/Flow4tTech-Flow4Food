# Pendências Manuais — Ações que Requerem Acesso Admin

Itens que não podem ser automatizados por falta de acesso admin. Cada item tem responsável e passos exatos.

---

## 🔴 1. Branch Protection Rules no GitHub

**Responsável:** `kaique-silvestre` (dono do repo)
**Repo:** `kaique-silvestre/Flow4tTech-Flow4Food`

### Como fazer

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
| Require branches to be up to date | ✅ |
| Do not allow bypassing the above settings | ✅ (opcional mas recomendado) |

> Os nomes `backend` e `frontend` são os job IDs exatos do `.github/workflows/ci.yml`.
> Eles só aparecem no dropdown depois que o CI rodar ao menos uma vez no branch.

---

## 🔴 2. Backup Automático do PostgreSQL Railway

**Responsável:** `kaique-silvestre` (dono do projeto Railway)
**Projeto Railway:** `delightful-passion`

### Diagnóstico

A opção de backup não foi encontrada no dashboard. Planos Railway:
- **Hobby** — sem backups automáticos de banco
- **Pro** — backups diários incluídos

### Opções

**Opção A — Upgrade de plano Railway (recomendado)**
Ir em Railway Dashboard → Settings → Billing → Upgrade to Pro.
Backups automáticos diários ficam disponíveis no serviço Postgres.

**Opção B — Script de backup externo (sem upgrade)**
Pode ser feito com `pg_dump` agendado via GitHub Actions ou cron externo.
Avisar para implementar se optar por esta via.

---

## 🟡 3. Frontend Staging no Vercel

**Responsável:** `kaique-silvestre` (dono do projeto Vercel do sistema)

### O que fazer

No Vercel dashboard do projeto do frontend (`Flow4Food` ou similar):

1. Settings → Git → conectar branch `staging`
2. Settings → Environment Variables → adicionar variável:
   - **Environment:** Preview (ou criar environment "Staging")
   - **Key:** `VITE_API_URL`
   - **Value:** URL do backend staging no Railway (ex: `https://flow4food-staging.up.railway.app`)
3. Fazer um push na branch `staging` para triggerar o deploy

### Como achar a URL do backend staging

Railway Dashboard → projeto `delightful-passion` → environment `staging` → serviço `Flow4Tech-Flow4Food` → Settings → Domains.

---

## Como marcar como resolvido

Quando um item for implementado, mover para `docs/dev-practices/historico-pendencias.md` com data de resolução.
