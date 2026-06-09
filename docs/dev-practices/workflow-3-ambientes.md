# Workflow de Desenvolvimento — 3 Ambientes

> **Objetivo central:** Nenhuma alteração de código ou schema chega ao banco do cliente sem passar por staging e aprovação manual.

---

## Índice

1. [Visão Geral da Arquitetura](#1-visão-geral-da-arquitetura)
2. [Os 3 Ambientes](#2-os-3-ambientes)
3. [Fluxo de Desenvolvimento Padrão](#3-fluxo-de-desenvolvimento-padrão)
4. [Trabalhando com Migrations](#4-trabalhando-com-migrations)
5. [Deploy em Produção](#5-deploy-em-produção)
6. [Como a Segurança de Tenant Funciona](#6-como-a-segurança-de-tenant-funciona)
7. [Variáveis de Ambiente](#7-variáveis-de-ambiente)
8. [Comandos de Referência Rápida](#8-comandos-de-referência-rápida)
9. [O que NÃO Fazer](#9-o-que-não-fazer)
10. [Pendências Críticas](#10-pendências-críticas)
11. [Procedimentos de Emergência](#11-procedimentos-de-emergência)

---

## 1. Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUXO DE CÓDIGO                          │
│                                                             │
│  developer  →  development  →  staging  →  production       │
│  (local)       (branch)       (Railway)   (Railway)        │
│                                                             │
│  Banco local   Banco local   Banco staging  Banco cliente  │
│  (Postgres)    (Postgres)    (Railway PG)   (Railway PG)   │
└─────────────────────────────────────────────────────────────┘
```

**Regra de ouro:** código sobe automaticamente para staging. Para produção, migrations são sempre **manuais** e **deliberadas**.

---

## 2. Os 3 Ambientes

### 2.1 Development (Local)

| Item | Valor |
|---|---|
| Branch Git | `development` |
| Banco | `localhost:5432/matchpoint` |
| Backend | `http://localhost:8000` |
| Frontend | `http://localhost:5173` |
| `ENV` | `dev` |
| Migrations | Manuais (`alembic upgrade head`) |
| Docs Swagger | Disponíveis em `/docs` |

**Quando usar:** desenvolvimento de features, testes, debugging.

### 2.2 Staging (Railway)

| Item | Valor |
|---|---|
| Branch Git | `staging` |
| Banco | Railway Postgres (environment staging) |
| Backend | URL do Railway staging |
| `ENV` | `staging` |
| Migrations | **Automáticas** no startup (`alembic upgrade head && uvicorn`) |
| Docs Swagger | Indisponível |

**Quando usar:** validar que a feature funciona em ambiente real antes de ir pra prod. Banco vazio, sem dados de cliente.

**Como deployar:** `git push origin staging` — Railway detecta e deploya automaticamente.

### 2.3 Production (Railway)

| Item | Valor |
|---|---|
| Branch Git | `main` |
| Banco | Railway Postgres (environment production) |
| Backend | URL de produção |
| `ENV` | `prod` |
| Migrations | **MANUAIS** — nunca automáticas |
| Docs Swagger | Indisponível |

**Quando usar:** após validação completa em staging. Contém dados reais do cliente.

**Como deployar:** push pra `main` sobe o código; migration roda separadamente (ver seção 5).

---

## 3. Fluxo de Desenvolvimento Padrão

### Passo a passo para qualquer feature

```
1. development  →  2. staging  →  3. prod
```

#### Passo 1 — Desenvolver localmente

```powershell
# Certifique-se de estar na branch correta
git checkout development

# Crie uma branch de feature a partir de development
git checkout -b feature/nome-da-feature

# ... desenvolva ...

# Rode o backend local
cd backend
.venv\Scripts\Activate.ps1
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Rode o frontend local (outro terminal)
cd frontend
npm run dev
```

Se a feature inclui migration:
```powershell
cd backend
.venv\Scripts\Activate.ps1
alembic revision --autogenerate -m "descricao_da_migration"
# Revise o arquivo gerado antes de rodar!
alembic upgrade head
```

#### Passo 2 — Testar em Staging

```powershell
# Merge da feature branch em development
git checkout development
git merge feature/nome-da-feature

# Merge de development em staging
git checkout staging
git merge development
git push origin staging
# Railway detecta e deploya automaticamente + roda migrations
```

Verifique no Railway dashboard que o deploy foi `SUCCESS` antes de continuar.

#### Passo 3 — Subir para Produção

```powershell
# Merge de staging em main
git checkout main
git merge staging
git push origin main
# Railway deploya o código — SEM rodar migration

# Se houve migration: aplique manualmente (ver seção 5)
```

---

## 4. Trabalhando com Migrations

### Regras fundamentais

1. **Nunca edite** uma migration que já foi aplicada em produção
2. **Sempre revise** o arquivo gerado pelo autogenerate — ele erra bastante
3. **Teste em staging primeiro** — staging roda do zero a cada ciclo
4. **Migrations são código** — revisão obrigatória antes de merge em `main`

### Criando uma migration nova

```powershell
cd backend
.venv\Scripts\Activate.ps1

# Gera baseado nas mudanças nos models (autogenerate)
alembic revision --autogenerate -m "add_coluna_x_em_tabela_y"

# Ou cria em branco (para migrações de dados, DDL manual, etc.)
alembic revision -m "seed_dados_iniciais"
```

O arquivo será criado em `backend/alembic/versions/`. **Sempre abra e revise** antes de rodar.

### Coisas que o autogenerate não detecta

- Criação/alteração de RLS policies
- Criação de roles e permissões PostgreSQL
- Triggers e funções PL/pgSQL
- `FORCE ROW LEVEL SECURITY`
- Índices compostos customizados
- Mudanças em `server_default` com expressões complexas

Para essas, escreva a migration manualmente usando `op.execute(sa.text(...))`.

### Checklist antes de commitar uma migration

- [ ] Arquivo tem `revision` e `down_revision` corretos na cadeia
- [ ] `upgrade()` e `downgrade()` implementados
- [ ] Para tabelas com tenant: inclui `tenant_id`, FK pra `tenants`, RLS policy, index
- [ ] Para tabelas novas com RLS: inclui `ENABLE ROW LEVEL SECURITY`, `FORCE ROW LEVEL SECURITY`, policy e trigger `trg_set_tenant_id`
- [ ] Testou `alembic upgrade head` localmente do zero (banco limpo)
- [ ] Testou `alembic downgrade -1` e depois `upgrade head` novamente

### Convenção de nomes

```
NNNN_verbo_objeto.py

Exemplos:
0050_add_observacoes_to_comandas.py
0051_create_notificacoes_push.py
0052_seed_planos_default.py
```

### Como checar estado atual

```powershell
alembic current          # revision aplicada no banco
alembic history          # histórico de todas as migrations
alembic heads            # cabeças atuais (deve ser 1 só)
alembic check            # verifica se há migrations pendentes
```

---

## 5. Deploy em Produção

### Processo completo

```
Push main  →  Railway deploya código  →  Verificar saúde  →  Rodar migration manual  →  Verificar novamente
```

#### 5.1 Push do código

```powershell
git checkout main
git merge staging
git push origin main
```

Railway detecta o push e deploya automaticamente. **O código sobe, mas a migration NÃO roda.**

#### 5.2 Verificar saúde do deploy

No Railway dashboard: confirmar que o deployment está `SUCCESS`.

Ou via MCP Railway: verificar status do serviço.

#### 5.3 Aplicar migration (se houver)

No **Railway Console** (dashboard → serviço → aba Console):

```bash
/opt/venv/bin/alembic upgrade head
```

**Antes de rodar:**
- [ ] Confirmar que o staging rodou a mesma migration sem erros
- [ ] Verificar horário (prefira horário de baixo uso do cliente)
- [ ] Avisar o cliente se a migration for longa ou impactar disponibilidade

#### 5.4 Verificar após migration

```bash
/opt/venv/bin/alembic current
# Deve mostrar a revision esperada com (head)
```

### Quando NÃO há migration

Se o push for só código (sem mudança de schema), não precisa de nada além do push. O Railway deploya e o app reinicia automaticamente.

---

## 6. Como a Segurança de Tenant Funciona

### Visão geral

O sistema usa **Row-Level Security (RLS) do PostgreSQL** para garantir que cada tenant veja apenas seus próprios dados — mesmo que haja um bug no código.

### Camadas de proteção

```
Request HTTP
    ↓
JWT validation (token do usuário contém tenant_id)
    ↓
get_tenant_db() em dependencies.py
    ↓
SET LOCAL ROLE app_user          ← muda para role restrita
SET LOCAL app.tenant_id = X      ← define tenant na sessão PG
    ↓
SQLAlchemy query
    ↓
PostgreSQL RLS policy filtra automaticamente por tenant_id
    ↓
Resultado: apenas linhas do tenant X
```

### Por que o FORCE ROW LEVEL SECURITY importa

Por padrão no PostgreSQL, o **owner da tabela bypassa RLS**. O usuário `matchpoint` (que o app usa) é o owner. Sem `FORCE ROW LEVEL SECURITY`, uma query que roda como `matchpoint` veria dados de todos os tenants.

A migration `0049` corrigiu isso adicionando `FORCE ROW LEVEL SECURITY` em todas as 23 tabelas.

### Tabelas com RLS (23 no total)

**Da migration 0043:** categorias, fornecedores, insumos, produtos, movimentos_estoque, compras, comandas, itens_comanda, pagamentos, comissoes_garcom, eventos_comanda, profile_permissions, profiles, system_users

**Da migration 0044:** caixa_sessoes, caixa_movimentos

**Da migration 0047:** garcons, metodos_pagamento, contas_pagar, notificacoes, estabelecimento, ficha_tecnica, itens_compra

### Template para nova tabela com RLS

Toda tabela nova que contém dados de tenant deve seguir este padrão na migration:

```python
def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    op.create_table(
        "nome_tabela",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.BigInteger(),
                  sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
                  nullable=False),
        # ... outras colunas ...
    )

    op.create_index("ix_nome_tabela_tenant_id", "nome_tabela", ["tenant_id"])

    if is_pg:
        bind.execute(sa.text("ALTER TABLE nome_tabela ENABLE ROW LEVEL SECURITY"))
        bind.execute(sa.text("ALTER TABLE nome_tabela FORCE ROW LEVEL SECURITY"))
        bind.execute(sa.text(
            "CREATE POLICY tenant_isolation ON nome_tabela "
            "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::bigint)"
        ))
        bind.execute(sa.text(
            "ALTER TABLE nome_tabela "
            "ALTER COLUMN tenant_id SET DEFAULT "
            "(NULLIF(current_setting('app.tenant_id', true), ''))::bigint"
        ))
        bind.execute(sa.text(
            "CREATE TRIGGER trg_set_tenant_id "
            "BEFORE INSERT ON nome_tabela "
            "FOR EACH ROW EXECUTE FUNCTION set_tenant_id()"
        ))
```

---

## 7. Variáveis de Ambiente

### Backend

| Variável | Dev | Staging | Prod |
|---|---|---|---|
| `DATABASE_URL` | `postgresql://matchpoint:matchpoint@localhost:5432/matchpoint` | Railway Postgres staging | Railway Postgres prod |
| `JWT_SECRET` | Qualquer string ≥32 chars | Secret exclusivo staging | Secret exclusivo prod (rotacionado) |
| `ENV` | `dev` | `staging` | `prod` |
| `CORS_ORIGINS` | `http://localhost:5173,...` | URL frontend staging | URL frontend prod |
| `JWT_EXPIRES_MINUTES` | 15 | 15 | 15 |
| `REFRESH_TOKEN_EXPIRES_DAYS` | 7 | 7 | 7 |

**Regras:**
- `JWT_SECRET` deve ser **diferente** em cada ambiente
- Nunca commitar `.env` no git (já está no `.gitignore`)
- Rotacionar `JWT_SECRET` de prod invalida todos os tokens existentes — avisar o cliente

### Frontend

| Variável | Dev | Prod |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | URL do Railway prod |

---

## 8. Comandos de Referência Rápida

### Backend (PowerShell, dentro de `backend/`)

```powershell
# Ativar venv
.venv\Scripts\Activate.ps1

# Rodar backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Migrations
alembic upgrade head              # aplicar todas pendentes
alembic current                   # ver revision atual
alembic history                   # ver histórico
alembic downgrade -1              # reverter última
alembic revision --autogenerate -m "descricao"   # gerar nova
alembic check                     # verificar pendentes
```

### Frontend (PowerShell, dentro de `frontend/`)

```powershell
npm run dev          # rodar dev server
npm run build        # build de produção
npm run type-check   # verificar tipos TypeScript
npm run lint         # rodar ESLint
```

### Git — fluxo típico

```powershell
# Nova feature
git checkout development
git checkout -b feature/minha-feature
# ... desenvolve ...
git add arquivo.py
git commit -m "feat: descrição da feature"

# Subir para staging
git checkout staging
git merge feature/minha-feature
git push origin staging

# Subir para prod (após validação em staging)
git checkout main
git merge staging
git push origin main
```

### Verificar estado das migrations em prod

No Console do Railway (environment production):
```bash
/opt/venv/bin/alembic current
/opt/venv/bin/alembic history --verbose | head -20
```

---

## 9. O que NÃO Fazer

### Migrations

- **NÃO** edite uma migration já aplicada em prod (crie uma nova)
- **NÃO** faça `alembic upgrade head` em prod de forma automática
- **NÃO** commite migrations com dados hardcoded de tenant (`tenant_id = 1`, `tenant_id = 2`)
- **NÃO** crie tabela de tenant sem RLS policy e FORCE ROW LEVEL SECURITY

### Git

- **NÃO** faça merge direto de `development` para `main` — sempre passe por `staging`
- **NÃO** force-push em `main` ou `staging`
- **NÃO** commite arquivos `.env` ou segredos

### Produção

- **NÃO** edite dados diretamente no banco de prod via psql/Console sem backup
- **NÃO** troque `JWT_SECRET` de prod sem avisar o cliente (invalida todos os logins)
- **NÃO** faça deploy de prod em horário de pico de uso do cliente

---

## 10. Pendências

### 10.1 Role `app_user` não existe no banco

**Risco:** ALTO — sem essa role, `SET ROLE app_user` falha ou é ignorado. RLS pode não estar sendo aplicado corretamente.

**O que é:** `dependencies.py` executa `SET ROLE app_user` a cada request autenticado. Essa role PostgreSQL precisa existir e ter permissões restritas para que o RLS funcione como esperado.

**Fix necessário:** Criar migration que:
1. Cria a role `app_user` se não existir
2. Concede permissões de `SELECT/INSERT/UPDATE/DELETE` nas tabelas tenant-isoladas
3. **NÃO** concede `BYPASSRLS` para essa role

```sql
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
    CREATE ROLE app_user;
  END IF;
END $$;

GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
REVOKE ALL ON alembic_version FROM app_user;
```

**Investigar primeiro:** Verificar se a role existe no banco de prod antes de criar a migration.

### 10.2 CI/CD automatizado ✅ Implementado

Pipeline GitHub Actions operacional: lint, types, build, migrations, testes. Branch protection ativa em `staging` e `main`. Ver `ci-cd.md` para detalhes.

**Ainda faltam:** testes de integração reais no backend (hoje pytest passa com `continue-on-error`).

### 10.3 Frontend staging sem URL própria

**Status:** Frontend não tem deploy próprio apontando para o backend staging.

**Workaround atual — testar staging localmente:**

```powershell
# 1. Criar arquivo frontend/.env.staging.local (não commitado)
# VITE_API_URL=https://flow4tech-flow4food-staging.up.railway.app

# 2. Rodar frontend localmente com a variável sobrescrita
cd frontend
$env:VITE_API_URL="https://flow4tech-flow4food-staging.up.railway.app"
npm run dev
```

Acessar `http://localhost:5173` — frontend local, banco de staging.

**Fix definitivo (Vercel):** Configurar preview deployment no Vercel para branch `staging`:
1. Vercel dashboard → projeto → Settings → Environment Variables
2. Adicionar `VITE_API_URL = https://flow4tech-flow4food-staging.up.railway.app`
3. Scope: apenas branch `staging` (não afeta produção)
4. Após configurar: todo push em `staging` gera preview URL com frontend + backend staging juntos

### 10.4 Backup automatizado do banco de prod

**Risco:** ALTO — Railway não garante backup automático no plano básico.

**Ação:** Verificar no Railway dashboard (serviço Postgres → aba Backups) se backups automáticos estão ativos. Se não, considerar upgrade de plano ou configurar pg_dump periódico via cron no Railway.

---

## 11. Procedimentos de Emergência

### Reverter migration em produção

```bash
# No Console do Railway (production)
/opt/venv/bin/alembic downgrade -1    # volta uma migration
/opt/venv/bin/alembic current          # confirmar revision
```

Depois, reverter o código no git:
```powershell
git checkout main
git revert HEAD  # ou git reset --hard <commit-anterior>
git push origin main
```

### Rollback completo de deploy

No Railway dashboard: aba **Deployments** → encontrar último deploy bom → **Redeploy**.

### Banco de prod inacessível / corrompido

1. Não entre em pânico — Railway tem backups internos
2. Acesse Railway dashboard → serviço Postgres → aba **Backups**
3. Restaure o backup mais recente antes do incidente
4. **Avise o cliente imediatamente** com tempo estimado de retorno

### JWT secret comprometido

1. Gere novo secret: `python -c "import secrets; print(secrets.token_hex(32))"`
2. Atualize `JWT_SECRET` no Railway (environment production → Variables)
3. Todos os usuários serão deslogados — é esperado
4. Avise o cliente antes se possível

---

## Apêndice — Estrutura de Branches

```
main (produção — dados do cliente)
  ↑ merge após validação
staging (pré-produção — banco limpo Railway)
  ↑ merge após testes locais  
development (integração local)
  ↑ merge de feature branches
feature/xxx (desenvolvimento de features individuais)
```

## Apêndice — IDs Railway

> Guardar em local seguro (não commitar)

- Project ID: `f5927c27-99fc-4328-99dc-8ace97bc8d22`
- Environment production ID: `e151fb0e-f2b1-4201-854c-163dd35e9b0b`
- Environment staging ID: `53ca76a7-543e-43c5-9dfe-3dcd860f097b`
- Service backend ID: `c5ffe6aa-07d6-45cc-b1a3-d033276a6e87`
- Service Postgres ID: `8368993e-15fb-4c6c-b22e-c68eeb2bc485`
