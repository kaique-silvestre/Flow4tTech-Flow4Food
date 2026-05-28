# Plano Final — Auth, Multi-tenant e Permissões

Adaptação do `login.md` ao sistema atual com roadmap multi-restaurante.

## 0. Nomenclatura

- **Flow4Food** = sistema de gestão de restaurante (este repositório). Produto independente, funciona standalone.
- **Flow4Tech** = portal/empresa. Site de entrada. Hoje sem integração técnica com Flow4Food — só um link externo no portal pra URL do Flow4Food.

Flow4Food deve operar sem nenhuma dependência de Flow4Tech: login, gestão de usuários, criação de restaurantes — tudo local.

## 1. Arquitetura

- **Tenancy:** Shared DB Postgres no Railway + `estabelecimento_id` em toda tabela operacional + RLS habilitado.
- **Auth:** Local apenas. Username + senha (bcrypt). Sem SSO, sem IdP externo.
- **Sessão:** Access token JWT curto (15-30min) + refresh token longo (7-30d) armazenado no DB com rotação obrigatória.
- **Permissões:** Estilo AWS IAM — tabela de Allow explícito. Cada linha = 1 permissão concedida. Ausência de linha = deny implícito. Admin curto-circuita.
- **Provisionamento de estabelecimento + admin:** feito pela equipe Flow4Tech via CLI (não self-service, não exposto na web).

## 2. Modelo de Dados

### Novas tabelas

`usuarios`
- `id`, `estabelecimento_id` (FK, NOT NULL), `nome`, `username`, `senha_hash` (NOT NULL), `is_admin` (boolean), `ativo` (boolean), `senha_temporaria` (boolean — força reset no primeiro login), `created_at`
- Unique `(estabelecimento_id, username)`

`permissoes` (estilo AWS Allow)
- `id` (BIGINT PK)
- `usuario_id` (FK `usuarios`, NOT NULL)
- `estabelecimento_id` (FK `estabelecimentos`, NOT NULL) — pra RLS
- `recurso` (string, ex: `comandas`)
- `acao` (string, ex: `criar`)
- `created_at`
- `created_by` (FK `usuarios`, quem concedeu)
- Unique `(usuario_id, recurso, acao)`
- Indexes: `(usuario_id)`, `(estabelecimento_id)`

Cada linha = 1 Allow. Sem booleans, sem JSON. Conceder = INSERT. Revogar = DELETE. Lista de permissões do user = `SELECT recurso, acao FROM permissoes WHERE usuario_id=X`.

`audit_log` (criada vazia, instrumentação fase 2)
- `id`, `estabelecimento_id`, `usuario_id`, `acao`, `recurso`, `detalhes` (JSONB), `timestamp`

`tenant_counters` (numerações por tenant)
- `estabelecimento_id`, `contador` (ex: `comanda_numero`), `valor`
- PK `(estabelecimento_id, contador)`

`refresh_tokens`
- `id` (BIGINT PK)
- `usuario_id` (FK `usuarios`, NOT NULL)
- `estabelecimento_id` (FK `estabelecimentos`, NOT NULL) — pra RLS
- `token_hash` (SHA-256 do refresh token, NOT NULL, unique)
- `expires_at` (TIMESTAMP NOT NULL)
- `revoked` (BOOLEAN, default false)
- `revoked_at` (TIMESTAMP, nullable)
- `revoked_reason` (`logout` | `rotation` | `reuse_detected` | `admin` | `expired` | `password_change`)
- `replaced_by_id` (FK self, nullable) — rastreia cadeia de rotação
- `device_info` (JSONB, nullable: `{ user_agent, ip }`)
- `created_at`, `last_used_at`
- Indexes: `(usuario_id, revoked)`, `(token_hash)`, `(expires_at)`
- RLS: `tenant_isolation` por `estabelecimento_id`

### Tabela existente

`estabelecimentos` (já existe) — vira multi-linha. Mantém campos atuais.

### `estabelecimento_id` em todas operacionais

`comandas`, `itens_comanda`, `pagamentos`, `eventos_comanda`, `produtos`, `categorias`, `ficha_tecnica`, `componentes_ficha`, `insumos`, `movimentos_estoque`, `compras`, `fornecedores`, `garcons`, `comissoes_garcom`, `metodos_pagamento`.

NOT NULL FK. Index composto começando por `estabelecimento_id`. Uniques existentes viram compostos.

### Recursos de permissão (7)

`comandas`, `cardapio`, `estoque`, `compras`, `fornecedores`, `garcons`, `financeiro`, `configuracoes`.

(Sem "usuarios" — gestão exclusiva do admin. Sem "mesas"/"caixa" — não existem no sistema.)

### Ações canônicas (MVP)

`visualizar`, `criar`, `editar`, `excluir`.

Futuro: novas ações = só strings novas em `acao`, sem ALTER TABLE. Exemplos planejáveis: `aplicar_desconto`, `cancelar`, `fechar`, `reabrir`.

### Drop

`config_seguranca` (após migration de bootstrap).

## 3. Migration

Faseada, zero-downtime:

1. Criar `usuarios`, `permissoes`, `audit_log`, `tenant_counters`, `refresh_tokens`
2. Adicionar `estabelecimento_id` nullable em todas operacionais
3. Backfill: garantir 1 linha em `estabelecimentos` (id=1), preencher `estabelecimento_id=1` em todas operacionais
4. Criar admin local a partir de `config_seguranca` (username=`admin`, hash existente, `is_admin=true`, `ativo=true`, `senha_temporaria=true`, `estabelecimento_id=1`)
5. `estabelecimento_id` NOT NULL + FK + index em todas operacionais
6. Uniques compostos: refazer `unique_insumo_nome` (migration 0021) como `(estabelecimento_id, nome)`, idem outras
7. Habilitar RLS + policies (ver §6)
8. CHECK/trigger: FKs cross-tabela validam mesmo `estabelecimento_id`
9. Drop `config_seguranca`

## 4. Backend — Autenticação

### Login

`POST /auth/login`
- Body: `{ username, senha }`
- Username case-insensitive
- Valida user existe + ativo + senha correta
- Como tenant é resolvido sem usuário escolher: `username` é unique globalmente (não por tenant). Decisão pragmática — pequenos restaurantes, baixo risco de colisão. Reavaliar se >100 tenants.
- Resposta inclui flag `senha_temporaria` — frontend força tela de troca de senha antes de prosseguir.
- Retorna par de tokens (ver Tokens).

### Tokens

**Access token (JWT)**
- HS256 local
- Duração: `ACCESS_TOKEN_DURATION` (default 1800s / 30min)
- Payload: `{ sub: user_id, estabelecimento_id, is_admin, exp }`
- Sem permissões (vão ao DB)
- Stateless, não revogável individualmente — depende de expiração curta

**Refresh token**
- String aleatória 256 bits (`secrets.token_urlsafe(32)`)
- Armazenado **apenas como SHA-256 hash** em `refresh_tokens.token_hash`
- Duração: `REFRESH_TOKEN_DURATION` (default 30d)
- Rotação obrigatória: cada uso gera novo, revoga anterior (`revoked_reason=rotation`, `replaced_by_id` aponta novo)
- Detecção de roubo: uso de token já revogado → revoga toda cadeia + todos refresh tokens do user (`revoked_reason=reuse_detected`) + log de segurança

**Resposta padrão de login/refresh:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "rt_...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Endpoints

`POST /auth/refresh`
- Body: `{ refresh_token }`
- Valida: existe, não revogado, não expirado, user `ativo=true`
- Rotação: revoga atual (`rotation`), emite novo par
- Detecção de roubo: se já revogado, marca toda cadeia + todos tokens do user como `reuse_detected`, retorna 401
- Atualiza `last_used_at`
- Rate limit: 10 req/min por `token_hash`
- 401 em qualquer falha de validação

`POST /auth/logout`
- Header: `Authorization: Bearer <access_token>`
- Body: `{ refresh_token }`
- Revoga refresh token informado (`revoked_reason=logout`)
- Access token continua válido até expirar (stateless)
- 204 No Content

`POST /auth/logout-all`
- Header: `Authorization: Bearer <access_token>`
- Revoga todos refresh tokens ativos do `user_id` (`revoked_reason=logout`)
- 204 No Content

`POST /auth/change-password`
- Header: `Authorization: Bearer <access_token>`
- Body: `{ senha_atual, senha_nova }`
- Valida senha atual, atualiza hash, marca `senha_temporaria=false`
- Revoga todos refresh tokens (`revoked_reason=password_change`)
- Retorna novo par de tokens (sessão atual continua)

`GET /auth/sessions`
- Lista sessões ativas do user atual
- Retorna `[{ id, device_info, created_at, last_used_at }]`

`DELETE /auth/sessions/{id}`
- Revoga sessão específica do próprio user
- Admin pode revogar sessão de outro user do mesmo tenant via `DELETE /admin/users/{user_id}/sessions/{id}`

`GET /auth/me`
- Retorna `{ user, estabelecimento, permissoes: [{ recurso, acao }] }`
- Frontend consome no boot

### Configuração

`.env`:
```
ACCESS_TOKEN_DURATION=1800        # 30min
REFRESH_TOKEN_DURATION=2592000    # 30d
REFRESH_TOKEN_ROTATION=true
REFRESH_TOKEN_CLEANUP_GRACE=2592000
```

### Provisionamento de Estabelecimento

Sem endpoint público de signup. Equipe Flow4Tech provisiona via CLI:

```
python -m src.scripts.provision_estabelecimento
```

Interativo. Pede: `nome_estabelecimento`, `cnpj?`, `admin_nome`, `admin_username`, `admin_senha_inicial`. Cria `estabelecimento` + `usuario` (`is_admin=true`, `senha_temporaria=true`). Equipe entrega credenciais ao cliente por canal externo (email/whatsapp). Cliente troca senha no primeiro login.

Migration 0xxx (passo 4 acima) é caso especial: cria admin a partir de `config_seguranca` pra manter compat com instância atual.

Sem `/auth/setup` HTTP. Self-service eliminado.

## 5. Backend — Autorização

### Dependency

`require_permission(recurso: str, acao: str)`

- Compõe com `get_current_user`, `get_current_tenant`
- Admin (`is_admin=true`): curto-circuita, sempre passa
- Não admin: `SELECT 1 FROM permissoes WHERE usuario_id=X AND recurso=Y AND acao=Z`. Existe = allow. Não existe = 403.
- Cross-tenant access = 404 (não 403, evita enumeration)
- Cache opcional em memória (TTL 30s) — invalidar em mutação de permissão

### Repository base

`query_tenant(model)` injeta `WHERE estabelecimento_id = current_tenant`. Todo service usa. Refactor gradual.

### Engine abstraída

`get_db(tenant_id)` dependency. Hoje retorna engine único. Futuro: cache de engines por tenant (multi-DB ready).

### Gestão de Permissões (admin)

`GET /admin/users` — lista usuários do tenant

`POST /admin/users` — cria usuário (admin define `is_admin`, lista de permissões iniciais)

`PATCH /admin/users/{id}` — edita nome/username/ativo

`POST /admin/users/{id}/password` — admin reseta senha (marca `senha_temporaria=true`, revoga refresh tokens)

`GET /admin/users/{id}/permissions` — lista Allow rows do user

`POST /admin/users/{id}/permissions` — Body: `{ recurso, acao }`. INSERT row.

`DELETE /admin/users/{id}/permissions` — Body: `{ recurso, acao }`. DELETE row.

`POST /admin/users/{id}/permissions/bulk` — Body: `{ grants: [...], revokes: [...] }`. Transação única. UX da tela admin (checkboxes em lote) usa este.

Tudo gated por `is_admin=true` (não vira permissão concedível — admin é exclusivo).

## 6. RLS Postgres

Habilitar em todas operacionais + `usuarios`, `permissoes`, `refresh_tokens`, `audit_log`, `tenant_counters`:

```sql
ALTER TABLE comandas ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON comandas
  USING (estabelecimento_id = current_setting('app.tenant_id')::int);
```

Middleware FastAPI: por request, `SET LOCAL app.tenant_id = <jwt.estabelecimento_id>` antes do handler.

Roles Postgres:
- `flow4food_app`: sem `BYPASSRLS`. App usa.
- `flow4food_admin`: com `BYPASSRLS`. Scripts internos (CLI provisionamento), migrations.

## 7. Frontend

### Login

`LoginPage`:
- Campos: `username` + `senha`
- Sem botões de SSO/integração externa
- Se resposta `senha_temporaria=true` → redireciona pra tela "Trocar Senha" antes de liberar app

### `authStore`

```ts
{
  accessToken: string | null,
  refreshToken: string | null,
  tokenExpiresAt: number | null,
  user: { id, nome, username, is_admin, senha_temporaria } | null,
  estabelecimento: { id, nome } | null,
  permissoes: Array<{ recurso: string, acao: string }>,
}
```

Persistência: `localStorage` via `zustand/persist`. Refresh em cookie HttpOnly fica como decisão adiada.

Hidrata via `GET /auth/me` no boot.

### Interceptor Axios

Refresh automático em 401. Single-flight: múltiplas requests em paralelo aguardam mesma promessa de refresh.

```ts
let refreshPromise: Promise<TokenPair> | null = null;

axios.interceptors.response.use(
  r => r,
  async (error) => {
    const original = error.config;
    if (error.response?.status !== 401 || original._retry) return Promise.reject(error);
    original._retry = true;

    try {
      refreshPromise ??= callRefresh(useAuthStore.getState().refreshToken!);
      const tokens = await refreshPromise;
      refreshPromise = null;
      useAuthStore.getState().setTokens(tokens);
      original.headers.Authorization = `Bearer ${tokens.access_token}`;
      return axios(original);
    } catch (e) {
      refreshPromise = null;
      useAuthStore.getState().clear();
      window.location.href = "/login";
      return Promise.reject(e);
    }
  }
);
```

### Permissão na UI

Hook `usePermission(recurso, acao)` checa se par existe em `authStore.permissoes` (ou retorna `true` se `is_admin`). Esconde itens de menu/sidebar, desabilita botões. Backend sempre revalida (403).

### Tela admin

`/configuracoes/usuarios`:
- Lista usuários do tenant
- Criar/editar usuário
- Editar permissões: grid recursos × ações com checkboxes. Submit chama `POST /admin/users/{id}/permissions/bulk` com diff (grants + revokes).
- Ativar/desativar (revoga sessões)
- Reset senha (revoga sessões, marca temporária)
- Bloqueado: editar próprio `is_admin`, desativar a si mesmo

`/conta/sessoes`:
- Lista próprias sessões ativas
- Revogar sessão específica
- "Sair de todos dispositivos"

`/conta/senha`:
- Trocar própria senha (revoga outras sessões)

## 8. Integridade

- ≥1 admin ativo por estabelecimento: service check antes de desativar/remover admin
- Admin não remove próprio `is_admin`, não desativa a si mesmo, não muda próprio `estabelecimento_id`
- Soft delete (`ativo=false`). Hard delete proibido.
- Username único globalmente (decisão MVP, ver §4 Login)

## 9. Logout e Revogação

### Cenários

| Cenário | Ação |
|---------|------|
| Logout normal | `POST /auth/logout` revoga refresh token informado |
| Logout em todos dispositivos | `POST /auth/logout-all` revoga todos refresh tokens do user |
| Admin desativa user | Marca `ativo=false` + revoga todos refresh tokens (`reason=admin`) |
| Troca de senha (própria) | Revoga outras sessões (`reason=password_change`), emite novos tokens |
| Admin reseta senha de outro user | Revoga todos refresh tokens do alvo (`reason=admin`) |
| Detecção de roubo (reuse) | Revoga toda cadeia + todos refresh tokens do user (`reason=reuse_detected`) |
| Token expirado | Sem ação ativa; cleanup job remove depois |

### Limite de impacto do access token

Access token stateless = não revogável individualmente. Aceitável porque:
- Duração 30min limita janela de exposição
- Permissão verificada no DB a cada request → mudança imediata
- User desativado: dependency `get_current_user` checa `ativo=true` no DB → 401 imediato

### Cleanup automático

Job agendado (cron Railway ou APScheduler in-process):
```sql
DELETE FROM refresh_tokens
WHERE expires_at < NOW() - INTERVAL '30 days'
   OR (revoked = true AND revoked_at < NOW() - INTERVAL '7 days');
```
Frequência: diária, fora do horário de pico.

### Rate limiting

- `/auth/refresh`: 10 req/min por `token_hash`
- `/auth/login`: 5 req/min por IP + 10 req/min por `username`

## 10. Audit Log

Tabela criada agora. Instrumentação fase 2. Chamadas explícitas em services pra ações de negócio (criar comanda, dar desconto, fechar caixa, alterar permissão, criar/desativar usuário). Sem middleware genérico.

## 11. Identificadores

- Username: `^[a-z0-9._-]{3,30}$`, comparação case-insensitive, único globalmente
- Senha: mín 8 chars, bcrypt
- Esqueci senha: admin reseta manualmente. Admin esquece: CLI `python -m src.scripts.reset_admin <username>`

## 12. Pré-requisitos pra futuro multi-DB

(Custo zero agora, paga depois se migrar)

- `estabelecimento_id` rigoroso em toda tabela
- FKs cross-tabela mesmo tenant (CHECK/trigger)
- Sequences via `tenant_counters`, não sequence Postgres global
- Engine abstraída via `get_db(tenant_id)`
- Sem tabela compartilhada cross-tenant
- Sem JOIN cross-tenant
- Migrations idempotentes (Alembic já cobre)

## 13. PR Slicing

1. **Multi-tenant base + RLS:** migration `estabelecimento_id` em todas tabelas, backfill, uniques compostos, indexes, RLS policies, roles Postgres, middleware `SET LOCAL app.tenant_id`, repository helper, dependency `get_db(tenant_id)`, `tenant_counters`
2. **Auth local + access token:** modelos `usuarios`/`permissoes`/`audit_log`, CLI `provision_estabelecimento`, login username/senha (retorna só access token nesta fase), `/auth/me`, dependency `require_permission` + aplicado em router piloto (comandas), drop `config_seguranca`
3. **Refresh tokens + logout:** modelo `refresh_tokens` (com RLS), `/auth/refresh` com rotação + detecção de reuse, `/auth/logout`, `/auth/logout-all`, `/auth/change-password`, `/auth/sessions`, rate limit, cleanup job. Login passa a retornar par access+refresh.
4. **Authorization roll-out + admin CRUD:** `require_permission` em todos routers + endpoints `/admin/users/*` (criar, editar, ativar/desativar, reset senha, gerenciar permissões com Allow rows)
5. **Frontend:** login novo, store com access+refresh+expiresAt, interceptor Axios single-flight, hide UI por permissão, tela admin de usuários (com grid de permissões), tela "minhas sessões", tela troca de senha, fluxo de `senha_temporaria` no primeiro login

## 14. Decisões Adiadas (fase 2+)

- Integração técnica com portal Flow4Tech (SSO, API server-to-server) — hoje só link externo
- Refresh tokens em cookie `HttpOnly; Secure` (MVP usa localStorage)
- Refresh proativo no frontend (timer pré-expiração)
- Audit log instrumentação completa
- Permissões em ações não-CRUD (`aplicar_desconto`, `cancelar`, etc) — modelo já suporta, falta usar
- Multi-DB / DB-per-tenant
- Username unique por tenant (hoje global)

## 15. Edge Cases Cobertos

- Deploy zero / instância nova: migration bootstrap cria admin a partir de `config_seguranca`. Novas instalações: CLI provisiona.
- JWT existente (sub: "estabelecimento"): `JWT_SECRET` bump força relogin
- Cliente vira gigante: extração via `pg_dump --where="estabelecimento_id=X"` viável
- Vazamento cross-tenant: RLS Postgres garante isolamento mesmo se app esquecer filtro
- Refresh token roubado: rotação + detecção de reuse → invalida toda cadeia + todas sessões
- User desativado com access token válido: dependency revalida `ativo=true` no DB → 401 imediato
- Multi-tab/multi-device: cada sessão = 1 refresh token. Logout single revoga só corrente. Logout-all revoga todas.
- Primeiro login pós-provisionamento: `senha_temporaria=true` força troca antes de usar app
- Permissão nova (ex: `aplicar_desconto`): só adicionar string no enum de ações + checagem no endpoint. Sem migration.

## 16. Testes Essenciais

### Auth
- Login com credenciais válidas retorna par access + refresh
- Login com `senha_temporaria=true` retorna flag, frontend força tela de troca
- Login com user `ativo=false` retorna 401
- Rate limit login: 6ª tentativa em 1min mesmo IP retorna 429

### Refresh Tokens
- `/auth/refresh` com token válido retorna novo par e revoga anterior (`rotation`)
- `/auth/refresh` com token revogado por rotação detecta reuse → revoga toda cadeia + todos refresh tokens do user (`reuse_detected`), retorna 401
- `/auth/refresh` com token expirado retorna 401
- `/auth/refresh` com user `ativo=false` retorna 401
- `/auth/logout` revoga refresh token informado
- `/auth/logout-all` revoga todos refresh tokens do user
- `/auth/change-password` revoga outras sessões mas mantém atual
- Admin desativa user → todos refresh tokens revogados
- Admin reseta senha → todos refresh tokens revogados
- Frontend retenta request original após refresh automático
- Múltiplas requests paralelas em 401 compartilham 1 chamada `/auth/refresh`
- Cleanup job remove tokens expirados >30d e revogados >7d

### Permissões
- INSERT row em `permissoes` → endpoint correspondente passa
- DELETE row → endpoint correspondente retorna 403
- Admin sem nenhuma row em `permissoes` ainda acessa tudo (curto-circuito)
- Não-admin sem row de `comandas:visualizar` retorna 403 ao listar comandas
- Cross-tenant: user de tenant A tenta acessar comanda de tenant B → 404 (RLS oculta)
- Bulk update: grants + revokes em transação única, rollback se falhar

### RLS
- Refresh token de tenant A não é visível pra sessão de tenant B
- `permissoes` de tenant A não é visível pra sessão de tenant B
- Comanda de tenant A não é visível pra sessão de tenant B
- Role `flow4food_admin` (BYPASSRLS) usada por CLI/migrations enxerga tudo
