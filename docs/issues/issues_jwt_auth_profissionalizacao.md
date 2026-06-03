# Issues — JWT Auth: Profissionalização

**Parent PRD:** `docs/prds/prd_jwt_auth_profissionalizacao.md`
**Gerado em:** 2026-05-24

Três issues mapeadas em 3 PRs. Issue 1 sem blockers — pode ir hoje. Issues 2 e 3 bloqueadas por Issue 1 (dependem do `jti` no token e da migração pyjwt), mas são independentes entre si e podem ser desenvolvidas em paralelo.

---

## Visão geral — grafo de dependências

```
Issue 1 — Fase 1: Correções críticas (sem infra)
    │
    ├── Issue 2 — Fase 2: Logout com blacklist Postgres
    │
    └── Issue 3 — Fase 3+4: Refresh token + access token em memória
```

---

## Issue 1 — Fase 1: Correções críticas de autenticação ✅

**Tipo:** Security
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Quatro correções independentes no mesmo PR, todas na camada de autenticação:

1. **Remover bypass de permissões legado:** a condição `if "user_id" in payload` em `require_permission` concede acesso irrestrito a tokens sem `user_id`. Remover a condição — qualquer token sem `user_id` é rejeitado com 403. Tokens sem `user_id` não devem existir mais (fluxo legado é código morto).

2. **Corrigir expiração hardcoded:** `create_access_token` usa `timedelta(hours=8)` ignorando `JWT_EXPIRES_HOURS` do config. Substituir pelo valor do `Settings`. Atualizar `.env` com `JWT_EXPIRES_HOURS=1` para produção (60 min — refresh token manterá a sessão na Fase 3).

3. **Aumentar exigência do JWT_SECRET:** `min_length=8` em `config.py` é insuficiente para HS256. Aumentar para `min_length=32`. Gerar novo segredo forte (`python -c "import secrets; print(secrets.token_hex(32))"`) e atualizar em Railway e `.env` local antes do deploy.

4. **Migrar `python-jose` → `pyjwt`:** substituir `python-jose[cryptography]` por `pyjwt[crypto]` no `pyproject.toml`. Trocar todos os imports `from jose import jwt, JWTError` por `import jwt` e `from jwt.exceptions import InvalidTokenError`. Ajustar assinaturas de `jwt.encode` e `jwt.decode` para a API do pyjwt. `pyjwt` verifica tokens emitidos com HS256 pelo `python-jose` com o mesmo segredo — sem logout forçado de usuários ativos ao fazer deploy.

### Critérios de aceite

- [x] Request com token sem campo `user_id` para rota com `require_permission` → resposta 403.
- [x] Request com token com `user_id` mas sem a permissão da tela → resposta 403.
- [x] Request com token com `user_id` e permissão correta → resposta 200.
- [x] Token gerado após deploy tem `exp` calculado com `JWT_EXPIRES_HOURS` do config (não mais 8h fixo).
- [x] Inicializar backend com `JWT_SECRET` de menos de 32 chars → erro na startup, aplicação não sobe.
- [x] `python-jose` removido de `pyproject.toml`; `pyjwt[crypto]` adicionado.
- [x] `jwt.encode` e `jwt.decode` funcionam corretamente com HS256.
- [x] Login, `/me` e rotas protegidas funcionam normalmente após a troca de biblioteca.
- [x] Nenhuma regressão em rotas de reset de senha ou change-password.

### Testes

- Token sem `user_id` → `require_permission` lança 403.
- Token com `user_id` sem a permissão → 403.
- Token com `user_id` e permissão → 200 e payload retornado.
- `create_access_token` com `JWT_EXPIRES_HOURS=2` → `exp` do payload é `now + 2h` (margem de 5s).

### Bloqueado por

Nenhum. Mas: **atualizar `JWT_SECRET` no Railway e `.env` local antes de fazer o deploy** (não após).

### User stories endereçadas

- US1: token sem `user_id` rejeitado com 403
- US2: `JWT_SECRET` de menos de 32 chars rejeita na startup
- US3: expiração configurável via `JWT_EXPIRES_HOURS`
- US4: backend usa `pyjwt` sem CVEs históricos

---

## Issue 2 — Fase 2: Logout com blacklist no Postgres ✅

**Tipo:** Security
**Bloqueado por:** Issue 1 (depende do campo `jti` adicionado ao token e da migração pyjwt)

### O que construir

Hoje o `/logout` não faz nada no servidor — o token continua válido até expirar. Implementar revogação real via blacklist no Postgres:

1. **Campo `jti` no token:** `create_access_token` passa a incluir `jti = str(uuid.uuid4())` no payload de cada token emitido.

2. **Tabela `revoked_tokens`:** migration Alembic com colunas `id`, `jti VARCHAR UNIQUE`, `expires_at TIMESTAMPTZ`. Índice em `jti` para lookup O(log n).

3. **Repositório `revoked_tokens_repository`:** três funções — `revoke(db, jti, expires_at)`, `is_revoked(db, jti) → bool`, `delete_expired(db)`.

4. **Verificação no `get_current_user`:** após `jwt.decode`, chamar `is_revoked(jti)`. Se verdadeiro, lançar 401 "Token revogado".

5. **Endpoint `/logout` efetivo:** receber payload via `Depends(get_current_user)`, extrair `jti` e `exp`, chamar `revoke(jti, exp)`. Retornar 204.

6. **Job de limpeza:** adicionar `delete_expired_revoked_tokens` ao APScheduler já configurado. Rodar a cada hora. Remove linhas com `expires_at < now()`.

### Critérios de aceite

- [x] Novo campo `jti` (UUID v4 string) presente em todo token emitido após o deploy.
- [x] Tabela `revoked_tokens` criada via migration Alembic sem afetar dados existentes.
- [x] `POST /auth/logout` com token válido → 204 e token adicionado à blacklist.
- [x] Request imediatamente após logout com o mesmo token → 401 "Token revogado".
- [x] Token expirado naturalmente não precisa estar na blacklist para ser rejeitado (jwt.decode já lança erro de expiração).
- [x] Dois usuários diferentes: logout de um não afeta sessão do outro.
- [x] Job de limpeza remove registros com `expires_at` no passado e preserva os válidos.
- [x] Tokens emitidos antes do deploy (sem `jti`) continuam funcionando normalmente (campo `jti` ausente = não verificado na blacklist).
- [x] Nenhuma regressão em rotas protegidas para usuários que não fizeram logout.

### Testes

- `is_revoked(jti)` retorna `False` para `jti` não registrado.
- Após `revoke(jti, exp_futuro)`, `is_revoked(jti)` retorna `True`.
- `delete_expired()` com 3 registros (2 expirados, 1 válido) → remove 2, mantém 1.
- Request a rota protegida com token revogado → 401.
- Request a rota protegida com token válido após logout de outro usuário → 200.

### Bloqueado por

Issue 1 (pyjwt instalado, `jti` adicionado ao token).

### User stories endereçadas

- US5: token invalidado imediatamente no logout
- US6: request com token revogado recebe 401
- US7: blacklist limpa automaticamente via scheduler
- US8: cada token tem `jti` único

---

## Issue 3 — Fase 3+4: Refresh token httpOnly + access token em memória ✅

**Tipo:** Security + Feature
**Bloqueado por:** Issue 1 (depende da estrutura pyjwt e config)

### O que construir

Dois problemas resolvidos juntos (devem ser deployados no mesmo PR backend+frontend):

**Problema 1 (Fase 3):** acesso token expira em 60 min e usuário é deslogado abruptamente. Sem renovação silenciosa.

**Problema 2 (Fase 4):** access token no `localStorage` é legível por qualquer XSS. Mover para memória RAM.

**Solução conjunta:** access token em memória (some ao fechar aba) + refresh token em cookie `httpOnly` (persiste entre abas/sessões). Frontend renova o access token silenciosamente via interceptor axios. Cookie `SameSite=None; Secure` obrigatório para funcionar entre Railway (backend) e Vercel (frontend) — dominios diferentes.

#### Backend

1. **Config:** adicionar `REFRESH_TOKEN_EXPIRES_DAYS: int = 7`.

2. **Tabela `refresh_tokens`:** migration Alembic com `id`, `user_id FK→system_users`, `token_hash VARCHAR(64) UNIQUE`, `expires_at TIMESTAMPTZ`, `revoked_at TIMESTAMPTZ nullable`, `created_at`. Hash SHA-256 do token — nunca o token bruto.

3. **Repositório `refresh_tokens_repository`:** `create(db, user_id, token_hash, expires_at)`, `get_by_hash(db, token_hash) → RefreshToken | None`, `revoke(db, id)`, `revoke_all_for_user(db, user_id)`, `delete_expired(db)`.

4. **Serviço de refresh token em `auth_service`:** `create_refresh_token(db, user_id) → str` (gera token aleatório, persiste hash). `rotate_refresh_token(db, raw_token) → tuple[str, str]` (valida, revoga antigo, emite novo access_token + novo refresh_token). `revoke_all_refresh_tokens(db, user_id)`.

5. **`POST /auth/login`:** além do `access_token` no body, setar cookie: `httponly=True, secure=True, samesite="none", max_age=REFRESH_TOKEN_EXPIRES_DAYS*86400`.

6. **`POST /auth/refresh`:** novo endpoint. Lê cookie `refresh_token`. Chama `rotate_refresh_token`. Seta novo cookie. Retorna `{ access_token }`.

7. **`POST /auth/logout`:** chamar `revoke_all_refresh_tokens(user_id)` além da blacklist do access token (Issue 2). Limpar cookie com `response.delete_cookie("refresh_token", samesite="none", secure=True)`.

8. **Job de limpeza:** adicionar `delete_expired_refresh_tokens` ao APScheduler. Rodar diariamente.

#### Frontend

9. **`authStore.ts`:** remover `persist` e o middleware do Zustand. Store em memória pura — `token: null` ao carregar a página/aba.

10. **`api.ts`:** adicionar `withCredentials: true` no `axios.create`. Adicionar interceptor de response: em 401 sem `_retry`, pausar fila de requests falhos, chamar `POST /auth/refresh` com `withCredentials: true`, se sucesso retentar toda a fila com novo token; se falha, limpar store e redirecionar `/login`. Fila evita N chamadas paralelas ao `/refresh`.

### Critérios de aceite

- [x] `POST /login` retorna `{ access_token }` no body E seta cookie `refresh_token` (`httponly`, `secure`, `samesite=none`).
- [x] Fechar aba e reabrir → `authStore.token` é `null`, mas `POST /auth/refresh` com cookie ativo reemite access token automaticamente (transparente para o usuário via interceptor).
- [x] `POST /auth/refresh` com cookie válido → 200 + novo `access_token` + cookie rotacionado.
- [x] `POST /auth/refresh` com cookie expirado → 401 → frontend redireciona `/login`.
- [x] `POST /auth/refresh` com cookie revogado (pós-logout) → 401 → frontend redireciona `/login`.
- [x] `POST /auth/logout` → access token na blacklist + refresh tokens do usuário revogados + cookie deletado.
- [x] 3 requests paralelos que recebem 401 → apenas 1 chamada ao `/refresh` → as 3 requests retentadas.
- [x] `localStorage` não contém mais `matchpoint_jwt` após o deploy.
- [x] Tabela `refresh_tokens` armazena hash SHA-256, nunca o token bruto.
- [x] Job de limpeza remove refresh tokens expirados diariamente.
- [x] Deploy backend Fase 3 sem frontend correspondente não é permitido (quebra a sessão de todos).

### Testes

- `create_refresh_token` persiste hash SHA-256 (não o raw token).
- `rotate_refresh_token` com token válido → retorna novo access_token e novo refresh_token; token antigo revogado.
- `rotate_refresh_token` com token revogado → lança 401.
- `rotate_refresh_token` com token expirado → lança 401.
- `revoke_all_refresh_tokens(user_id)` → todos os tokens daquele user_id com `revoked_at` preenchido; outros users não afetados.
- Após logout, `POST /auth/refresh` com cookie do token revogado → 401.
- `authStore` sem `persist` → `token` é `null` em store recém-iniciada.

### Bloqueado por

Issue 1. Pode ser desenvolvida em paralelo com Issue 2, mas **o deploy deve ser atômico: backend + frontend no mesmo release**. Não subir backend da Fase 3 sem o frontend correspondente.

### User stories endereçadas

- US5 (refresh): sessão renovada silenciosamente
- US6: sessão restaurada ao reabrir browser
- US7: logout invalida todos os tokens
- US8: `REFRESH_TOKEN_EXPIRES_DAYS` configurável
- US9: hash SHA-256 no banco
- US10: cookie `httpOnly; Secure; SameSite=None`
- US11: frontend retenta requests após 401 transparentemente
- US12: fila de requests paralelos — 1 chamada ao `/refresh`
- US13: `localStorage` não armazena mais o access token

---

## Resumo — gh commands

```bash
# Issue 1 (pode criar agora)
gh issue create \
  --title "security: JWT auth — fix bypass permissões, expiração, secret min-length, migrar pyjwt" \
  --label "security,backend" \
  --body "Ver docs/issues/issues_jwt_auth_profissionalizacao.md — Issue 1"

# Issue 2 (criar após Issue 1 mergeada)
gh issue create \
  --title "security: logout efetivo com blacklist JWT no Postgres" \
  --label "security,backend" \
  --body "Ver docs/issues/issues_jwt_auth_profissionalizacao.md — Issue 2"

# Issue 3 (criar após Issue 1 mergeada)
gh issue create \
  --title "security: refresh token httpOnly + access token em memória" \
  --label "security,backend,frontend" \
  --body "Ver docs/issues/issues_jwt_auth_profissionalizacao.md — Issue 3"
```
