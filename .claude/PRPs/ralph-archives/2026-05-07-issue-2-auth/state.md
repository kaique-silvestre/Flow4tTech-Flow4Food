---
iteration: 1
max_iterations: 10
plan_path: ".claude/PRPs/plans/issue-2-auth.md"
started_at: "2026-05-07T00:00:00Z"
---

# Ralph Progress Log

## Codebase Patterns
- Backend usa `uv run` para rodar comandos Python (pyproject.toml com uv)
- Estrutura Deep Models: models → repositories → services → api/routes
- Exception handler global em `src/core/errors.py` — usar `AppError(ErrorCode.X, msg, http_status=N)`
- `ErrorCode.SENHA_INCORRETA` já definido em errors.py
- Settings via `get_settings()` (lru_cache) — importar de `src.core.config`
- Frontend usa `npm` (não pnpm/bun)
- Sonner toast: `toast.error()` persistente, `toast.success()` 2-3s
- Axios instance em `src/lib/api.ts` com baseURL via `VITE_API_URL`
- Auth store: Zustand com `persist` middleware → localStorage
- `src/core/errors.py` já tem `ErrorCode.SENHA_INCORRETA` e `ErrorCode.UNAUTHORIZED`
- **bcrypt 5.0.0 incompatível com passlib CryptContext** — usar `import bcrypt` direto (`bcrypt.hashpw`/`bcrypt.checkpw`), não `passlib.context.CryptContext`
- Python 3.9 target: usar `Optional[X]` não `X | None` syntax em type hints
- Zustand persist armazena JSON com key `{ state: {...}, version: 0 }` — api.ts deve usar `useAuthStore.getState().token` não `localStorage.getItem(key)` direto

## Iteration 1 - 2026-05-07T10:30:00Z

### Completed
- A1: migration `0002_auth.py` (tabela config_seguranca)
- A2: model `ConfigSeguranca` + models/__init__.py
- B1: `auth_repository.py` (get_config, upsert_config)
- B2: `auth_service.py` (hash_password via bcrypt direto, verify_password, create_access_token, authenticate com auto-provisioning)
- C1: `schemas/auth.py` (LoginRequest, TokenResponse)
- C2: `api/routes/auth.py` (POST /api/auth/login)
- C3: `api/dependencies.py` atualizado com get_current_user (HTTPBearer + jose)
- C4: `main.py` registra auth router
- D1: `tests/test_auth.py` — 5 cenários (auto-provision, login OK, senha errada, token expirado, rota sem token)
- E1: `stores/authStore.ts` (Zustand persist, matchpoint_jwt)
- F1: `lib/api.ts` atualizado para usar authStore.getState()
- G1-G3: LoginPage + useLogin + authSchemas
- H1-H4: RequireAuth + Topbar + Sidebar + AppLayout
- I1: App.tsx com rotas /login e autenticadas

### Validation Status
- Type-check: PASS
- Lint: PASS (ruff BE, eslint FE)
- Tests: PASS (8 BE, 3 FE)
- Build: PASS

### Learnings
- bcrypt 5.0.0 + passlib: incompatível. Usar bcrypt direto.
- Python 3.9: sem X|Y union syntax, usar Optional[X]
- Zustand persist: não ler localStorage diretamente — usar getState()

### Next Steps
- Issue #3: Cadastros base (Categorias, Fornecedores, Garçons, Métodos de Pagamento)
- Todas as rotas CRUD usam `Depends(get_current_user)`
- Sidebar ganha links reais para os módulos

---
