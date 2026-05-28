# JWT Authentication — Análise, Problemas e Plano de Profissionalização

## 1. Como funciona hoje

### Fluxo de login

```
Cliente  →  POST /auth/login  { identifier, password }
Backend  →  bcrypt.checkpw(password, hash_no_banco)
         →  monta payload com permissões do perfil
         →  jwt.encode(payload, JWT_SECRET, HS256)
         →  retorna { access_token, token_type: "bearer", expires_in: 28800 }
```

### Payload do token

```json
{
  "sub": "42",
  "user_id": 42,
  "tenant_id": 1,
  "username": "joao",
  "name": "João Silva",
  "profile_id": 3,
  "profile_name": "Vendedor",
  "permissions": ["vendas", "clientes"],
  "exp": 1748000000
}
```

### Validação por rota (backend)

```
Header: Authorization: Bearer <token>
  ↓
HTTPBearer extrai token
  ↓
jwt.decode() → valida assinatura HS256 + expiração
  ↓
require_permission("tela") → verifica "tela" in permissions[]
  ↓
Se OK → injeta payload no handler
```

### Armazenamento (frontend)

- Zustand `persist` → **localStorage**, chave `matchpoint_jwt`
- Payload decodificado no cliente via `atob()` (sem validar assinatura — correto para frontend)
- Axios interceptor injeta `Authorization: Bearer <token>` em toda requisição
- HTTP 401 → `clearToken()` + redireciona `/login`

---

## 2. Problemas identificados

### P1 — Expiração hardcoded ignora config (severidade: baixa)

**Arquivo:** `backend/src/services/auth_service.py:44`

```python
# ATUAL — ignora JWT_EXPIRES_HOURS do Settings
expire = datetime.now(timezone.utc) + timedelta(hours=8)
```

`Settings` define `JWT_EXPIRES_HOURS: int = 12`, mas nunca é usado. Expira em 8h independente do ambiente.

---

### P2 — Logout stateless sem blacklist (severidade: média)

**Arquivo:** `backend/src/api/routes/auth.py:33`

```python
@router.post("/logout", status_code=204)
def do_logout() -> None:
    return None  # faz literalmente nada no servidor
```

Token continua válido após logout até expirar. Se o token vazar após o usuário deslogar, ainda funciona.

---

### P3 — Bypass de permissão em tokens legados (severidade: alta)

**Arquivo:** `backend/src/api/dependencies.py:34`

```python
# tokens legados (sub=estabelecimento) não têm permissions[] — conceder acesso temporário
if "user_id" in payload and screen not in permissions:
    raise HTTPException(...)
```

Qualquer token sem `user_id` no payload **ignora todas as verificações de permissão** e acessa qualquer rota protegida. Se um token antigo ou forjado sem `user_id` vazar, é acesso total.

---

### P4 — Token em localStorage expõe a XSS (severidade: média)

**Arquivo:** `frontend/src/stores/authStore.ts:33`

```typescript
persist(... { name: "matchpoint_jwt" })  // salva em localStorage
```

Qualquer `<script>` injetado na página lê `localStorage.getItem("matchpoint_jwt")` e extrai o token completo com as permissões.

---

### P5 — Sem refresh token (severidade: média)

Token expira em 8h e o usuário é deslogado. Sem mecanismo de renovação silenciosa — experiência ruim em sessões longas.

---

### P6 — JWT_SECRET com mínimo de 8 chars é fraco (severidade: alta)

**Arquivo:** `backend/src/core/config.py:17`

```python
JWT_SECRET: str = Field(..., min_length=8, ...)
```

8 caracteres é insuficiente para HS256. Força bruta em segredos curtos é viável. Mínimo deve ser 32 caracteres (256 bits).

---

## 3. Plano de profissionalização

### Fase 1 — Correções críticas (sem refatoração arquitetural)

#### Fix P1: usar JWT_EXPIRES_HOURS do config

```python
# auth_service.py
def create_access_token(payload: dict) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRES_HOURS)
    return jwt.encode({**payload, "exp": expire}, settings.JWT_SECRET, algorithm="HS256")
```

#### Fix P3: remover bypass de tokens legados

```python
# dependencies.py
def _check(payload: dict = Depends(get_current_user)) -> dict:
    permissions: list[str] = payload.get("permissions", [])
    if screen not in permissions:
        raise HTTPException(status_code=403, detail=f"Sem permissão: {screen}")
    return payload
```

Remover o comentário e a condição `if "user_id" in payload`. Tokens sem `user_id` não devem existir mais.

#### Fix P6: aumentar mínimo do JWT_SECRET

```python
# config.py
JWT_SECRET: str = Field(..., min_length=32, description="Secret for signing JWT — mínimo 32 chars")
```

Gerar segredo forte:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

### Fase 2 — Logout com blacklist (Redis)

Adicionar Redis ao stack. No logout, guardar o `jti` (JWT ID) com TTL igual ao tempo restante do token.

#### Adicionar `jti` ao token

```python
# auth_service.py
import uuid

def create_access_token(payload: dict) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRES_HOURS)
    return jwt.encode(
        {**payload, "exp": expire, "jti": str(uuid.uuid4())},
        settings.JWT_SECRET,
        algorithm="HS256",
    )
```

#### Blacklist no logout

```python
# auth_service.py
def logout(token_payload: dict, redis_client) -> None:
    jti = token_payload.get("jti")
    exp = token_payload.get("exp")
    if jti and exp:
        ttl = exp - int(datetime.now(timezone.utc).timestamp())
        if ttl > 0:
            redis_client.setex(f"blacklist:{jti}", ttl, "1")
```

#### Verificar blacklist na validação

```python
# dependencies.py
def get_current_user(...) -> dict:
    payload = jwt.decode(...)
    jti = payload.get("jti")
    if jti and redis_client.exists(f"blacklist:{jti}"):
        raise HTTPException(status_code=401, detail="Token revogado")
    return payload
```

---

### Fase 3 — Refresh token

Dois tokens:
- **Access token:** curto (15–60 min), stateless
- **Refresh token:** longo (7–30 dias), armazenado em httpOnly cookie

#### Fluxo

```
Login → access_token (15min, no body) + refresh_token (7d, httpOnly cookie)

Requisição normal → usa access_token no header

access_token expirou →
  frontend chama POST /auth/refresh automaticamente (interceptor axios)
  backend valida refresh_token do cookie
  backend emite novo access_token
  frontend continua requisição original

Logout → invalida refresh_token no banco/Redis
```

#### Tabela no banco para refresh tokens

```sql
CREATE TABLE refresh_tokens (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES system_users(id),
    token_hash  VARCHAR(64) NOT NULL UNIQUE,  -- SHA-256 do token
    expires_at  TIMESTAMPTZ NOT NULL,
    revoked_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

Armazenar hash SHA-256 do token, nunca o token bruto.

#### Configuração de cookie (backend)

```python
# routes/auth.py
from fastapi import Response

@router.post("/login")
def do_login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    result = login(db, body.identifier, body.password)
    response.set_cookie(
        key="refresh_token",
        value=result.refresh_token,
        httponly=True,
        secure=True,        # só HTTPS
        samesite="strict",
        max_age=7 * 24 * 3600,
    )
    return TokenResponse(access_token=result.access_token)
```

#### Interceptor axios com retry automático

```typescript
// lib/api.ts
let isRefreshing = false;
let failedQueue: Array<{ resolve: (v: string) => void; reject: (e: unknown) => void }> = [];

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as AxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !original._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          original.headers!.Authorization = `Bearer ${token}`;
          return api(original);
        });
      }

      original._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post("/auth/refresh", {}, { withCredentials: true });
        const newToken = data.access_token;
        useAuthStore.getState().setToken(newToken);
        failedQueue.forEach((p) => p.resolve(newToken));
        failedQueue = [];
        original.headers!.Authorization = `Bearer ${newToken}`;
        return api(original);
      } catch {
        failedQueue.forEach((p) => p.reject(new Error("Session expired")));
        failedQueue = [];
        useAuthStore.getState().clearToken();
        window.location.assign("/login");
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
```

---

### Fase 4 — Migrar access token de localStorage para memória

```typescript
// authStore.ts — sem persist, token só em memória
export const useAuthStore = create<AuthState>()((set) => ({
  token: null,
  user: null,
  setToken: (t) => set({ token: t, user: parseJwtPayload(t) }),
  clearToken: () => set({ token: null, user: null }),
}));
```

Sem `persist` → token some ao fechar aba. Refresh token no cookie httpOnly mantém a sessão ativa. XSS não consegue mais ler o access token.

---

## 4. Resumo de prioridades

| Prioridade | Item | Fase | Esforço |
|---|---|---|---|
| CRÍTICO | Remover bypass de tokens legados (P3) | 1 | 5 min |
| CRÍTICO | Aumentar mínimo JWT_SECRET para 32 chars (P6) | 1 | 5 min |
| ALTO | Corrigir expiração hardcoded (P1) | 1 | 5 min |
| MÉDIO | Logout com blacklist Redis (P2) | 2 | 1–2 dias |
| MÉDIO | Refresh token + httpOnly cookie (P4/P5) | 3 | 2–3 dias |
| BAIXO | Migrar access token de localStorage para memória | 4 | 1 dia |

---

## 5. Estado atual vs. profissional

| Critério | Atual | Profissional |
|---|---|---|
| Algoritmo | HS256 | HS256 ✓ (ou RS256 se microserviços) |
| Segredo | mín. 8 chars | mín. 32 chars (256 bits) |
| Expiração | 8h hardcoded | configurável por env, 15–60 min |
| Logout | stateless (token segue válido) | blacklist Redis por `jti` |
| Sessão longa | usuário deslogado ao expirar | refresh token httpOnly cookie |
| Armazenamento front | localStorage (vulnerável a XSS) | memória RAM (access) + httpOnly cookie (refresh) |
| Permissão legada | bypass total | sem bypass — tokens sem `user_id` rejeitados |
| Rotação de segredo | manual/nunca | rotação via env sem downtime |
