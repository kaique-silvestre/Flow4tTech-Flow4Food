# PRP — Issue #2: Auth (Login único + JWT + sessão)

**Parent PRD:** `docs/prd_matchpoint_mvp.md`
**Parent Issue:** `docs/issues_matchpoint_mvp.md` → Issue 2
**Documento mestre:** `docs/matchpoint_documentacao.md`
**Type:** AFK
**Status:** Pronto para execução
**Criado em:** 2026-05-07
**Depende de:** Issue #1 (Foundation) — concluída

---

## Objetivo

Fluxo completo de autenticação por senha única do estabelecimento. Backend: migration criando tabela `config_seguranca`, endpoint `POST /api/auth/login`, geração de JWT (12h). Frontend: página `/login` com RHF+Zod, guard `<RequireAuth>`, interceptor axios, layout pai (Topbar + Sidebar placeholder) envolvendo rotas autenticadas.

---

## Estrutura de Arquivos a Criar/Modificar

```
backend/
  alembic/versions/
    0002_auth.py                          # migration: tabela config_seguranca
  src/
    models/
      auth.py                             # SQLAlchemy model ConfigSeguranca
    schemas/
      auth.py                             # Pydantic schemas (LoginRequest, TokenResponse)
    repositories/
      auth_repository.py                  # get_config, update_password_hash
    services/
      auth_service.py                     # verify_password, create_token, authenticate
    api/
      routes/
        auth.py                           # POST /api/auth/login
      dependencies.py                     # get_current_user (verify JWT)
    main.py                               # include auth router (modificar)
  tests/
    test_auth.py                          # 4 cenários

frontend/
  src/
    features/
      auth/
        LoginPage.tsx                     # página /login (RHF+Zod, toast erro)
        useLogin.ts                       # mutation hook
        authSchemas.ts                    # schema Zod loginForm
    stores/
      authStore.ts                        # Zustand: token, setToken, clearToken
    components/
      layout/
        AppLayout.tsx                     # Topbar + Sidebar + <Outlet>
        Topbar.tsx                        # barra superior com título + logout
        Sidebar.tsx                       # sidebar com links placeholder
      auth/
        RequireAuth.tsx                   # guard: redirect /login se sem token
    lib/
      api.ts                              # (modificar) interceptors com authStore
    App.tsx                               # (modificar) rotas /login e autenticadas
```

---

## Tarefas

### Bloco A — Backend: Migration + Model

- [ ] **A1.** Criar `backend/alembic/versions/0002_auth.py`:
  - `upgrade()`: `CREATE TABLE config_seguranca (id INTEGER PK, senha_hash VARCHAR NOT NULL)`. Sem seed (hash inserido pelo service na primeira execução).
  - `downgrade()`: `DROP TABLE config_seguranca`.

- [ ] **A2.** Criar `backend/src/models/auth.py`:
  ```python
  class ConfigSeguranca(Base):
      __tablename__ = "config_seguranca"
      id: Mapped[int] = mapped_column(Integer, primary_key=True)
      senha_hash: Mapped[str] = mapped_column(String, nullable=False)
  ```
  Importar em `models/__init__.py` para Alembic detectar.

### Bloco B — Backend: Repository + Service

- [ ] **B1.** Criar `backend/src/repositories/auth_repository.py`:
  - `get_config(db) -> ConfigSeguranca | None`: `SELECT * FROM config_seguranca LIMIT 1`.
  - `upsert_config(db, senha_hash: str) -> ConfigSeguranca`: insert ou update (upsert simples: delete + insert, ou ON CONFLICT).

- [ ] **B2.** Criar `backend/src/services/auth_service.py`:
  - `hash_password(plain: str) -> str`: `passlib.context.CryptContext(schemes=["bcrypt"]).hash(plain)`.
  - `verify_password(plain: str, hashed: str) -> bool`: `pwd_context.verify(plain, hashed)`.
  - `create_access_token(data: dict, expires_hours: int) -> str`: `jose.jwt.encode` com `exp = now + expires_hours`, `secret = settings.JWT_SECRET`, `algorithm = "HS256"`.
  - `authenticate(db, senha: str) -> str`: busca config, se não existe → cria hash da senha recebida (primeiro acesso auto-provisiona). Se existe → verify; falso → levanta `AppError(ErrorCode.SENHA_INCORRETA, "Senha incorreta", http_status=401)`. Retorna token.

  > Nota: auto-provisioning no primeiro acesso (se não há hash cadastrado, a primeira senha informada se torna a senha) — comportamento documentado no contrato.

- [ ] **B3.** Criar `backend/src/api/dependencies.py` (ou expandir existente):
  - `get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)) -> dict`: decodifica JWT com `jose.jwt.decode`; levanta HTTP 401 se inválido/expirado.
  - `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")` — só pra geração de spec, não precisamos do form OAuth2, usamos JSON.

### Bloco C — Backend: Route + Register

- [ ] **C1.** Criar `backend/src/api/routes/auth.py`:
  - `POST /api/auth/login`:
    - Body: `LoginRequest(senha: str)`.
    - Resposta 200: `TokenResponse(access_token: str, token_type: str = "bearer", expires_in: int = 43200)`.
    - Resposta 401: `{"error":{"code":"SENHA_INCORRETA","message":"Senha incorreta","field":null}}`.

- [ ] **C2.** Modificar `backend/src/main.py`:
  - `from src.api.routes import auth as auth_router`
  - `app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])`

### Bloco D — Backend: Tests

- [ ] **D1.** Criar `backend/tests/test_auth.py` com fixture `client` usando SQLite in-memory:
  - **Cenário 1 — Primeiro acesso (auto-provisioning):** POST `/api/auth/login` com `{"senha":"abc123"}` → 200, campo `access_token` presente.
  - **Cenário 2 — Login OK:** após provisionar, login com mesma senha → 200 + token válido.
  - **Cenário 3 — Senha errada:** login com senha diferente → 401 + `code == "SENHA_INCORRETA"`.
  - **Cenário 4 — Token expirado rejeitado:** gerar token com `exp` no passado; chamar rota protegida (health autenticada ou endpoint de teste) → 401.
  - **Cenário 5 — Rota protegida sem token:** chamar rota protegida sem header → 401.

### Bloco E — Frontend: Zustand Auth Store

- [ ] **E1.** Criar `frontend/src/stores/authStore.ts`:
  ```ts
  interface AuthState {
    token: string | null
    setToken: (t: string) => void
    clearToken: () => void
  }
  ```
  Persiste token em `localStorage` (usar `zustand/middleware` `persist` com `localStorage`).

### Bloco F — Frontend: Axios Interceptors

- [ ] **F1.** Modificar `frontend/src/lib/api.ts`:
  - Request interceptor: lê `authStore.getState().token`; se existe, adiciona header `Authorization: Bearer ${token}`.
  - Response interceptor: captura status 401 → chama `authStore.getState().clearToken()` → `window.location.href = "/login"`.

### Bloco G — Frontend: Login Feature

- [ ] **G1.** Criar `frontend/src/features/auth/authSchemas.ts`:
  ```ts
  export const loginSchema = z.object({
    senha: z.string().min(1, "Senha obrigatória"),
  })
  export type LoginFormValues = z.infer<typeof loginSchema>
  ```

- [ ] **G2.** Criar `frontend/src/features/auth/useLogin.ts`:
  - `useMutation` chamando `POST /api/auth/login`.
  - `onSuccess`: salva token via `authStore.setToken`, navega para `/` com `useNavigate`.
  - `onError`: `toast.error("Senha incorreta")` (sonner).

- [ ] **G3.** Criar `frontend/src/features/auth/LoginPage.tsx`:
  - `useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) })`.
  - Campo Input para senha (type="password"), botão "Entrar" (desabilitado durante mutação).
  - Chama `useLogin().mutate(data)` no `handleSubmit`.
  - Layout centralizado, logo/título "Matchpoint".
  - Toast vermelho persistente (sonner `toast.error`) em erro de auth.

### Bloco H — Frontend: Guard + Layout

- [ ] **H1.** Criar `frontend/src/components/auth/RequireAuth.tsx`:
  ```tsx
  const token = useAuthStore(s => s.token)
  if (!token) return <Navigate to="/login" replace />
  return <Outlet />
  ```

- [ ] **H2.** Criar `frontend/src/components/layout/Topbar.tsx`:
  - Título "Matchpoint" à esquerda.
  - Botão "Sair" à direita: chama `clearToken()` + navega `/login`.

- [ ] **H3.** Criar `frontend/src/components/layout/Sidebar.tsx`:
  - Links placeholder: Dashboard, Comandas, Estoque, Compras, Relatórios, Configurações.
  - Usar `NavLink` do react-router-dom para active state.
  - Por ora apenas links sem ícones (ícones virão no UX sweep Issue #14).

- [ ] **H4.** Criar `frontend/src/components/layout/AppLayout.tsx`:
  ```tsx
  <div className="flex h-screen">
    <Sidebar />
    <div className="flex flex-col flex-1 overflow-hidden">
      <Topbar />
      <main className="flex-1 overflow-auto p-4">
        <Outlet />
      </main>
    </div>
  </div>
  ```

### Bloco I — Frontend: Rotas

- [ ] **I1.** Modificar `frontend/src/App.tsx`:
  ```tsx
  <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route element={<RequireAuth />}>
      <Route element={<AppLayout />}>
        <Route path="/" element={<PlaceholderPage />} />
        {/* demais rotas autenticadas virão aqui nas issues seguintes */}
      </Route>
    </Route>
  </Routes>
  ```

---

## Validações

Rodar após cada bloco de mudanças:

### Backend
```bash
cd backend
ruff check . && ruff format --check .
mypy src
pytest -q
```

### Frontend
```bash
cd frontend
npm run lint
npm run type-check
npm run build
```

### Manual (smoke)
```bash
# Backend rodando: uvicorn src.main:app --reload (com .env configurado)
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"senha":"teste123"}' | python3 -m json.tool
# Esperado: {"access_token":"...","token_type":"bearer","expires_in":43200}
```

---

## Critérios de Aceite (do Issue #2)

- [ ] Schema: tabela `config_seguranca` com hash da senha única (bcrypt).
- [ ] Endpoint `POST /api/auth/login` recebe senha, retorna JWT ou 401 com `SENHA_INCORRETA`.
- [ ] JWT expira em 12h, segredo via `JWT_SECRET`.
- [ ] Frontend: tela `/login` com RHF+Zod, toast vermelho em senha incorreta.
- [ ] `<RequireAuth>` wrapper redireciona para `/login` se sem token.
- [ ] Interceptor axios injeta `Authorization: Bearer` em toda request e trata 401 (clear storage + redirect).
- [ ] Layout pai (Topbar + Sidebar) envolve rotas autenticadas (sidebar apenas com placeholders).
- [ ] Múltiplas sessões simultâneas funcionam (mesma senha, JWTs independentes).
- [ ] Testes: login OK, senha errada, token expirado rejeitado, rota protegida bloqueia sem token.

---

## Notas Importantes

- **Auto-provisioning:** Primeiro acesso sem senha cadastrada → a primeira senha informada é gravada como hash. Simplifica onboarding (sem seed de senha). Comportamento documentado; mudança vem via `PATCH /api/config/senha` (Issue #13).
- **Sem revogação de JWT:** MVP sem blacklist. Logout só limpa storage local. JWT antigo permanece válido até expirar. Documentado como contrato MVP.
- **Múltiplas sessões:** Como JWT é stateless e não há revogação, mesma senha gera JWTs independentes — múltiplas sessões funcionam por design.
- **OAuth2PasswordBearer:** Usado apenas para documentação OpenAPI automática. Login usa JSON body, não form data.
- **Sidebar placeholder:** Apenas links textuais. Ícones e colapso responsivo (≤1366px) ficam para Issue #14 (UX sweep).
- **Token storage:** localStorage — aceitável para MVP single-establishment. Risco de XSS documentado; httpOnly cookie seria upgrade pós-MVP.

---

## Tabela de Decisões

| Decisão | Valor | Origem |
|---------|-------|--------|
| Algoritmo hash | bcrypt via passlib | Issue #2 spec |
| Algoritmo JWT | HS256 | Padrão; RS256 desnecessário MVP |
| Expiração JWT | 12h | Issue #2 spec |
| Armazenamento FE | localStorage + Zustand persist | MVP simplicity |
| Auto-provisioning | Sim (primeira senha vira hash) | Simplifica onboarding |
| Revogação JWT | Não (MVP) | Issue #13 documenta contrato |

---

## Próximos Passos Pós-Conclusão

Issue #3 (Cadastros base) consome este foundation de auth:
- Todas as rotas de CRUD usam `Depends(get_current_user)`.
- Sidebar ganha links reais para Categorias, Fornecedores, Garçons, Métodos de Pagamento.
