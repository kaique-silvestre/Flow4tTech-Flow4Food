# PRD — Profissionalização da Autenticação JWT

**Data:** 2026-05-24
**Status:** Aprovado para implementação
**Fases:** 3 PRs independentes (Fase 1 → Fase 2 → Fase 3+4)

---

## Problem Statement

O sistema de autenticação JWT do Matchpoint foi construído de forma funcional mas apresenta vulnerabilidades de segurança e limitações que precisam ser corrigidas antes de o produto escalar:

1. **Bypass total de permissões:** Qualquer token sem o campo `user_id` no payload ignora completamente o sistema de controle de acesso, concedendo acesso irrestrito a todas as rotas protegidas. Um token forjado ou legado sem `user_id` é suficiente para um atacante acessar qualquer dado do sistema.

2. **Segredo JWT fraco:** O `JWT_SECRET` aceita mínimo de 8 caracteres — insuficiente para HS256. Segredos curtos são vulneráveis a força bruta offline caso o token vaze.

3. **Expiração ignorada:** O código define `timedelta(hours=8)` diretamente, ignorando a variável `JWT_EXPIRES_HOURS` configurada no `.env`. Operadores não conseguem ajustar o tempo de sessão sem alterar código.

4. **Logout stateless ineficaz:** O endpoint `/logout` não realiza nenhuma ação no servidor. Tokens continuam válidos até expirarem naturalmente — se um token vazar após o logout do usuário, o atacante mantém acesso por até 8 horas.

5. **Token armazenado em localStorage:** O access token é persistido no `localStorage` via Zustand `persist`. Qualquer script XSS injetado na página consegue ler o token completo com todas as permissões do usuário.

6. **Sem renovação silenciosa de sessão:** Após a expiração (8h), o usuário é deslogado abruptamente. Não há mecanismo de refresh token para manter sessões longas sem relogin.

7. **Biblioteca JWT com CVEs históricos:** O projeto usa `python-jose`, que possui vulnerabilidades documentadas (CVE-2022-29217) e está menos ativamente mantido do que `pyjwt`.

---

## Solution

Profissionalização em três fases independentes e deployáveis:

**Fase 1 — Correções críticas imediatas** (sem nova infraestrutura): remover bypass de permissões, aumentar exigência do segredo, corrigir expiração hardcoded, migrar para `pyjwt`.

**Fase 2 — Logout com blacklist** (nova tabela no Postgres): tokens revogados no logout são registrados com `jti` e TTL. Limpeza automática via APScheduler já instalado.

**Fase 3+4 — Refresh token + memória** (nova tabela + mudança de frontend): access token de 60 min renovado silenciosamente via refresh token em cookie `httpOnly`. Token saí do `localStorage` para memória RAM — XSS não consegue mais lê-lo.

---

## User Stories

### Fase 1 — Correções críticas

1. Como administrador de sistema, quero que tokens sem `user_id` sejam rejeitados com 403, para que tokens legados ou forjados não concedam acesso irrestrito às rotas protegidas.
2. Como administrador de sistema, quero que o `JWT_SECRET` exija mínimo de 32 caracteres, para que segredos fracos sejam rejeitados na inicialização da aplicação.
3. Como administrador de sistema, quero configurar o tempo de expiração do token via variável de ambiente `JWT_EXPIRES_HOURS`, para que diferentes ambientes (dev/prod) possam ter políticas de sessão distintas sem alterar código.
4. Como desenvolvedor, quero que o backend use `pyjwt` em vez de `python-jose`, para eliminar vulnerabilidades conhecidas da biblioteca de autenticação.

### Fase 2 — Logout efetivo com blacklist

5. Como usuário, quero que ao fazer logout meu token seja imediatamente invalidado no servidor, para que mesmo que o token vaze após o logout ele não possa ser usado.
6. Como usuário, quero que requisições com token revogado recebam 401, para que o frontend redirecione para login automaticamente.
7. Como administrador de sistema, quero que tokens expirados sejam removidos automaticamente da blacklist, para que a tabela não cresça indefinidamente.
8. Como desenvolvedor, quero que cada token tenha um identificador único (`jti`), para que a revogação seja precisa e não afete outros tokens do mesmo usuário.

### Fase 3 — Refresh token

9. Como usuário, quero que minha sessão seja renovada silenciosamente enquanto estiver ativo, para que não precise fazer login novamente durante o expediente.
10. Como usuário, quero que ao fechar o navegador e reabrir, minha sessão seja restaurada automaticamente (se dentro do prazo do refresh token), para não precisar fazer login toda vez.
11. Como usuário, quero que ao fazer logout todos os meus tokens sejam invalidados, para que nenhum dispositivo ou sessão anterior continue com acesso.
12. Como administrador de sistema, quero configurar o prazo do refresh token via `REFRESH_TOKEN_EXPIRES_DAYS`, para ajustar a política de sessão sem alterar código.
13. Como desenvolvedor, quero que o refresh token seja armazenado como hash SHA-256 no banco, para que a exposição do banco não comprometa tokens ativos.
14. Como desenvolvedor, quero que o refresh token seja enviado como cookie `httpOnly; Secure; SameSite=None`, para que JavaScript client-side nunca consiga lê-lo.

### Fase 4 — Access token fora do localStorage

15. Como usuário, quero que meu token de acesso não seja armazenado em disco, para que scripts maliciosos injetados na página não consigam extraí-lo.
16. Como desenvolvedor, quero que o frontend retente automaticamente requisições que falharam por expiração de token, para que o usuário não perceba a renovação silenciosa.
17. Como desenvolvedor, quero que múltiplas requisições paralelas que recebem 401 aguardem o refresh e sejam retentadas, em vez de disparar múltiplas chamadas ao endpoint `/refresh`.

---

## Implementation Decisions

### Módulos a criar ou modificar

#### Fase 1

- **Config (`config.py`):** aumentar `min_length` do `JWT_SECRET` de 8 para 32. Sem outras mudanças estruturais.
- **Token service (`auth_service.py`):** substituir `timedelta(hours=8)` por `timedelta(hours=settings.JWT_EXPIRES_HOURS)`. Trocar `from jose import jwt` por `import jwt` (pyjwt). Ajustar assinaturas de `jwt.encode` e `jwt.decode` para API do pyjwt.
- **Permission dependency (`dependencies.py`):** remover condição `if "user_id" in payload` e o bloco de bypass. Tokens sem `user_id` são rejeitados diretamente pelo `get_current_user` (campo obrigatório no payload). `require_permission` verifica apenas se `screen in permissions`.
- **Dependências (`pyproject.toml`):** substituir `python-jose[cryptography]` por `pyjwt[crypto]`.

#### Fase 2

- **Modelo `RevokedToken`:** tabela `revoked_tokens(id, jti VARCHAR UNIQUE, expires_at TIMESTAMPTZ)`. Índice em `jti` e `expires_at`.
- **Repositório `revoked_tokens_repository`:** funções `revoke(jti, expires_at)`, `is_revoked(jti) → bool`, `delete_expired()`.
- **Token service:** adicionar `jti = str(uuid.uuid4())` ao payload em `create_access_token`. Adicionar `blacklist_token(db, jti, exp)` que persiste no banco.
- **Permission dependency:** após `jwt.decode`, chamar `is_revoked(jti)` — se verdadeiro, lançar 401 "Token revogado".
- **Auth route `/logout`:** receber `payload` via `Depends(get_current_user)`, chamar `blacklist_token`. Retornar 204.
- **Scheduler:** adicionar job `delete_expired_revoked_tokens` rodando a cada hora via APScheduler já configurado.
- **Migration Alembic:** nova revisão criando tabela `revoked_tokens`.

#### Fase 3+4

- **Modelo `RefreshToken`:** tabela `refresh_tokens(id, user_id FK, token_hash VARCHAR(64) UNIQUE, expires_at TIMESTAMPTZ, revoked_at TIMESTAMPTZ, created_at)`.
- **Repositório `refresh_tokens_repository`:** funções `create(user_id, token_hash, expires_at)`, `get_by_hash(token_hash) → RefreshToken | None`, `revoke(id)`, `revoke_all_for_user(user_id)`, `delete_expired()`.
- **Token service:** `create_refresh_token(db, user_id) → str` (gera token aleatório, persiste hash SHA-256). `rotate_refresh_token(db, token) → tuple[str, str]` (valida, revoga antigo, emite novo access + refresh). `revoke_all_refresh_tokens(db, user_id)`.
- **Auth route `/login`:** além do `access_token` no body, chamar `response.set_cookie(key="refresh_token", httponly=True, secure=True, samesite="none", max_age=7*24*3600)`.
- **Auth route `POST /refresh`:** ler cookie `refresh_token`, chamar `rotate_refresh_token`, setar novo cookie, retornar novo `access_token`.
- **Auth route `/logout`:** chamar `revoke_all_refresh_tokens(user_id)` além da blacklist do access token. Limpar cookie com `response.delete_cookie("refresh_token", samesite="none", secure=True)`.
- **Config:** adicionar `REFRESH_TOKEN_EXPIRES_DAYS: int = 7`.
- **Migration Alembic:** nova revisão criando tabela `refresh_tokens`.
- **`authStore.ts`:** remover `persist` e middleware do Zustand. Store em memória pura. Token zerado ao fechar aba.
- **`api.ts`:** adicionar interceptor de response com fila de retry. Em 401 sem `_retry`: pausar fila, chamar `POST /auth/refresh` com `withCredentials: true`, se sucesso retentar fila toda com novo token; se falha, limpar store e redirecionar para `/login`. Adicionar `withCredentials: true` no `axios.create`.

### Decisões de CORS e cookies

- Backend Railway + Frontend Vercel = cross-origin. Cookie exige `SameSite=None; Secure`.
- `allow_credentials=True` já configurado no CORS middleware. Manter origins explícitas (não `*`).
- `withCredentials: true` deve ser adicionado ao `axios.create` default para que cookies sejam enviados em todas as requisições.

### Tempos de expiração

- Access token: 60 minutos (via `JWT_EXPIRES_HOURS=1` em prod).
- Refresh token: 7 dias (via `REFRESH_TOKEN_EXPIRES_DAYS=7`).
- Blacklist TTL: igual ao tempo restante do access token no momento do logout.

### Sequência de deploy

- Fase 1 deploy independente — sem migration, sem dependência.
- Fase 2 deploy independente — requer migration `revoked_tokens`.
- Fases 3+4 deploy conjunto — requer migration `refresh_tokens` + deploy frontend simultâneo. Não deployar backend Fase 3 sem o frontend correspondente (usuários perderiam sessão sem o interceptor de refresh).

---

## Testing Decisions

**O que faz um bom teste:** testa comportamento externo observável, não detalhes de implementação. Dado um input, verifica o output ou efeito colateral. Nunca mocka o próprio módulo sendo testado.

### `create_access_token`
- Verifica que o payload retornado decodificado contém todos os campos esperados (`user_id`, `permissions`, `jti`, `exp`).
- Verifica que `exp` respeita `JWT_EXPIRES_HOURS` do config.
- Verifica que token com secret diferente é rejeitado no decode.

### `require_permission` dependency
- Token sem `user_id` no payload → 401 (rejeitado pelo `get_current_user`).
- Token com `user_id` mas sem a permissão da tela → 403.
- Token com `user_id` e permissão correta → 200.
- Token revogado (Fase 2) → 401 "Token revogado".

### Blacklist service (Fase 2)
- `is_revoked(jti)` retorna `False` para jti não registrado.
- Após `revoke(jti, exp)`, `is_revoked(jti)` retorna `True`.
- `delete_expired()` remove registros com `expires_at` no passado e mantém os válidos.

### Refresh token service (Fase 3)
- `create_refresh_token` persiste hash SHA-256 (não o token bruto).
- `rotate_refresh_token` com token válido retorna novo access_token e novo cookie.
- `rotate_refresh_token` com token revogado → 401.
- `rotate_refresh_token` com token expirado → 401.
- `revoke_all_refresh_tokens(user_id)` invalida todos os tokens daquele usuário.
- Após logout, chamada a `/refresh` com o cookie antigo → 401.

**Prior art:** usar padrão de testes existente em `tests/` com `pytest` + `httpx` + banco de teste real (sem mock de DB, conforme prática do projeto).

---

## Out of Scope

- **RS256 / chaves assimétricas:** HS256 é suficiente para arquitetura monolítica single-service. RS256 só faz sentido em microserviços com múltiplos verificadores.
- **OAuth2 / SSO / login social:** fora do escopo desta iteração.
- **Multi-tenant JWT:** o `tenant_id` já está no payload. Lógica de isolamento por tenant não muda nesta PRD.
- **Rate limiting em `/login`:** proteção contra brute force de senha é escopo separado.
- **Rotação automática de JWT_SECRET sem downtime:** operação de infra manual, não abordada aqui.
- **Notificação de login em novo dispositivo:** fora de escopo.

---

## Further Notes

- Ao subir Fase 1, todos os usuários que tiverem tokens emitidos com `python-jose` serão deslogados se a assinatura mudar — mas como o `JWT_SECRET` não muda, `pyjwt` consegue verificar tokens antigos emitidos por `python-jose` com HS256. Validar em ambiente de staging antes do deploy.
- Gerar novo `JWT_SECRET` de 32+ chars: `python -c "import secrets; print(secrets.token_hex(32))"`. Trocar em todas as variáveis de ambiente (Railway + local `.env`) antes de fazer deploy da Fase 1.
- Fase 2 adiciona uma query de banco por request autenticado (verificação de blacklist). Monitorar latência pós-deploy. Se necessário, adicionar cache em memória com TTL de 1 min na aplicação.
- Fase 3: o cookie `SameSite=None; Secure` exige que o backend Railway responda obrigatoriamente via HTTPS em todas as chamadas de `/auth/refresh`. Verificar que Railway não expõe HTTP sem redirect.
