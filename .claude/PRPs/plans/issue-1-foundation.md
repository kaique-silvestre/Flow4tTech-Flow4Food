# PRP — Issue #1: Foundation (Skeleton + Observabilidade + Boot)

**Parent PRD:** `docs/prd_matchpoint_mvp.md`
**Parent Issue:** `docs/issues_matchpoint_mvp.md` → Issue 1
**Documento mestre:** `docs/matchpoint_documentacao.md`
**Type:** HITL (decisões arquiteturais iniciais)
**Status:** Pronto para execução
**Criado em:** 2026-05-06

---

## Objetivo

Criar o esqueleto inicial dos dois apps (backend FastAPI + frontend React/Vite) seguindo a arquitetura Deep Models definida no PRD §Implementation Decisions e na §10 do documento mestre. Sem feature de domínio — apenas plumbing: estrutura de pastas, providers globais, validação de env, health check, observabilidade.

Greenfield. Repo atualmente só contém `.claude/`, `docs/`. Após este plano, ambos apps rodam local com comandos de dev e validação funcionando.

---

## Estrutura Final Esperada

```
Flow4Tech-sistema-de-gestao/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   └── health.py
│   │   │   └── dependencies.py
│   │   ├── services/
│   │   │   └── __init__.py
│   │   ├── repositories/
│   │   │   └── __init__.py
│   │   ├── models/
│   │   │   └── __init__.py
│   │   ├── schemas/
│   │   │   └── __init__.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py            # Pydantic Settings, valida env
│   │   │   ├── database.py          # engine SQLAlchemy + session
│   │   │   ├── logging.py           # structlog setup
│   │   │   ├── sentry.py            # Sentry init (opcional em dev)
│   │   │   ├── errors.py            # exception handler global + códigos
│   │   │   └── middleware.py        # request_id middleware
│   │   ├── __init__.py
│   │   └── main.py                  # FastAPI app factory
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_health.py
│   ├── alembic/
│   │   ├── versions/
│   │   │   └── 0001_initial_empty.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── .env.example
│   ├── .gitignore
│   ├── Makefile
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── PlaceholderPage.tsx
│   │   ├── features/
│   │   │   └── .gitkeep
│   │   ├── components/
│   │   │   └── ui/
│   │   │       └── .gitkeep
│   │   ├── hooks/
│   │   │   └── .gitkeep
│   │   ├── stores/
│   │   │   └── .gitkeep
│   │   ├── schemas/
│   │   │   └── .gitkeep
│   │   ├── lib/
│   │   │   ├── api.ts                # axios + interceptors
│   │   │   ├── format.ts             # formatCurrency, formatDate
│   │   │   ├── queryClient.ts        # TanStack Query
│   │   │   └── sentry.ts             # Sentry FE init
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css                 # tailwind directives
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── components.json               # shadcn/ui config
│   ├── .env.example
│   ├── .eslintrc.cjs
│   ├── .gitignore
│   └── README.md
│
├── .gitignore                        # raiz
└── README.md                         # raiz
```

---

## Tarefas

### Bloco A — Backend

- [ ] **A1.** Criar `backend/pyproject.toml` com Python 3.11+, dependências:
  - Runtime: `fastapi`, `uvicorn[standard]`, `sqlalchemy>=2`, `alembic`, `pydantic>=2`, `pydantic-settings`, `psycopg2-binary` (ou `psycopg[binary]`), `structlog`, `sentry-sdk[fastapi]`, `python-jose[cryptography]`, `passlib[bcrypt]`.
  - Dev: `pytest`, `pytest-asyncio`, `httpx`, `ruff`, `mypy`.
  - Scripts/commands no `[tool.ruff]` e `[tool.mypy]` configurados.
- [ ] **A2.** Criar estrutura de pastas Deep Models conforme acima, com `__init__.py` em cada pacote.
- [ ] **A3.** `backend/src/core/config.py`: classe `Settings(BaseSettings)` com vars do PRD §10.7.6 (DATABASE_URL, JWT_SECRET, JWT_EXPIRES_HOURS=12, TZ=America/Sao_Paulo, CORS_ORIGINS, ENV, SENTRY_DSN_BACKEND). Usa `model_config = SettingsConfigDict(env_file=".env")`. Falha cedo se obrigatórias ausentes (DATABASE_URL, JWT_SECRET).
- [ ] **A4.** `backend/src/core/database.py`: `create_engine(settings.DATABASE_URL)`, `SessionLocal`, dependency `get_db`. `Base = declarative_base()`.
- [ ] **A5.** `backend/src/core/logging.py`: configura `structlog` com `JSONRenderer`, processadores para timestamp, level, context vars (request_id).
- [ ] **A6.** `backend/src/core/sentry.py`: `init_sentry(dsn)` — opcional, no-op se DSN vazio.
- [ ] **A7.** `backend/src/core/errors.py`: enum `ErrorCode` (vazio por enquanto, ex.: `INTERNAL_ERROR = "INTERNAL_ERROR"`). Classe `AppError(Exception)` com `code`, `message`, `field`, `http_status`. Função `register_exception_handlers(app)` que registra handlers para `AppError`, `HTTPException` e exception genérica retornando `{"error":{"code","message","field"}}`.
- [ ] **A8.** `backend/src/core/middleware.py`: `RequestIdMiddleware` adiciona `request_id` (uuid4) ao contexto do structlog e ao header da resposta.
- [ ] **A9.** `backend/src/api/routes/health.py`: `GET /health` testa conexão com DB (`SELECT 1`), retorna `{"status":"ok","db":"ok"|"error","version":"0.1.0"}`. Versão lida do pyproject ou hardcoded.
- [ ] **A10.** `backend/src/main.py`: factory `create_app()` que monta FastAPI, registra `CORSMiddleware` (allowlist via `settings.CORS_ORIGINS`), `RequestIdMiddleware`, exception handlers, init Sentry, inclui router de health. Variável `app = create_app()` no topo level para `uvicorn`.
- [ ] **A11.** `backend/.env.example`: todas as vars com valores de exemplo (DATABASE_URL apontando pra postgres local, JWT_SECRET="changeme", etc.).
- [ ] **A12.** `backend/alembic.ini` + `backend/alembic/env.py` configurados para usar `settings.DATABASE_URL` e `Base.metadata`. Primeira revision `0001_initial_empty.py` vazia (`def upgrade(): pass`).
- [ ] **A13.** `backend/tests/test_health.py`: usa `httpx.AsyncClient` com app FastAPI, testa `GET /health` retorna 200 e shape correto. Mockar DB se necessário (usar SQLite in-memory fixture).
- [ ] **A14.** `backend/Makefile` com targets: `install`, `dev` (uvicorn reload), `lint` (ruff check + mypy), `test` (pytest), `migrate` (alembic upgrade head), `format` (ruff format).
- [ ] **A15.** `backend/README.md` curto: setup (`pip install -e ".[dev]"` ou `uv sync`), comandos `make dev`, `make test`, `make lint`.
- [ ] **A16.** `backend/.gitignore`: `.env`, `__pycache__`, `*.pyc`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `dist/`, `*.egg-info`.

### Bloco B — Frontend

- [ ] **B1.** Criar `frontend/` via `npm create vite@latest frontend -- --template react-ts` (ou equivalente manual: `package.json` + `tsconfig.json` + `vite.config.ts`).
- [ ] **B2.** Instalar deps:
  - Runtime: `react`, `react-dom`, `react-router-dom`, `axios`, `@tanstack/react-query`, `zustand`, `react-hook-form`, `zod`, `@hookform/resolvers`, `sonner`, `date-fns`, `clsx`, `tailwind-merge`, `class-variance-authority`, `lucide-react`, `@sentry/react`.
  - Dev: `tailwindcss`, `postcss`, `autoprefixer`, `@types/react`, `@types/react-dom`, `typescript`, `eslint`, `@typescript-eslint/parser`, `@typescript-eslint/eslint-plugin`, `eslint-plugin-react`, `eslint-plugin-react-hooks`, `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom`.
- [ ] **B3.** Configurar TailwindCSS: `tailwind.config.js` (`content: ["./index.html","./src/**/*.{ts,tsx}"]`), `postcss.config.js`, diretivas em `src/index.css`.
- [ ] **B4.** Init shadcn/ui: criar `components.json` com aliases (`@/components`, `@/lib`, etc.), instalar componentes base mínimos: Button, Dialog, Input, Label, Toaster (sonner). Criar `src/lib/utils.ts` com helper `cn`.
- [ ] **B5.** Configurar path alias `@/` em `tsconfig.json` e `vite.config.ts`.
- [ ] **B6.** Criar estrutura de pastas (`pages/`, `features/`, `components/ui/`, `hooks/`, `stores/`, `schemas/`, `lib/`) com `.gitkeep` onde vazio.
- [ ] **B7.** `src/lib/api.ts`: instância axios com `baseURL: import.meta.env.VITE_API_URL`, interceptor de request injeta `Authorization: Bearer ${jwt}` (lê de localStorage), interceptor de response trata 401 (limpa storage, redirect `/login` — placeholder por enquanto).
- [ ] **B8.** `src/lib/format.ts`: `formatCurrency(value: number)` via `Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'})`, `formatDate(d: Date|string, fmt?: string)` via `date-fns/format` com `locale: ptBR`.
- [ ] **B9.** `src/lib/queryClient.ts`: instância `QueryClient` com defaults (staleTime 30s, retry 1).
- [ ] **B10.** `src/lib/sentry.ts`: `initSentry()` lê `VITE_SENTRY_DSN`, no-op se vazio.
- [ ] **B11.** `src/App.tsx`: monta `<BrowserRouter>` + `<QueryClientProvider>` + `<Toaster>` (sonner) + rota placeholder `/` → `<PlaceholderPage>`.
- [ ] **B12.** `src/pages/PlaceholderPage.tsx`: tela "Matchpoint MVP — em desenvolvimento". Usa Button shadcn pra mostrar toast sonner.
- [ ] **B13.** `src/main.tsx`: chama `initSentry()`, renderiza `<App>`.
- [ ] **B14.** `frontend/.env.example`: `VITE_API_URL=http://localhost:8000`, `VITE_SENTRY_DSN=`.
- [ ] **B15.** `frontend/.eslintrc.cjs` configurado para React + TS.
- [ ] **B16.** `frontend/package.json` com scripts: `dev` (`vite`), `build` (`tsc -b && vite build`), `preview`, `lint` (`eslint src --max-warnings 0`), `type-check` (`tsc --noEmit`), `test` (`vitest run`).
- [ ] **B17.** `frontend/.gitignore`: `node_modules`, `dist`, `.env`, `.env.local`, `*.log`.
- [ ] **B18.** `frontend/README.md` curto: `npm install`, `npm run dev`, scripts de validação.
- [ ] **B19.** Smoke test mínimo: `src/lib/format.test.ts` verifica `formatCurrency(80.10) === "R$ 80,10"` (tolerar non-breaking space).

### Bloco C — Raiz e versionamento

- [ ] **C1.** `/.gitignore` raiz: encaminha pros `.gitignore` específicos (ou consolidado básico).
- [ ] **C2.** `/README.md` raiz: visão geral do monorepo, links para `docs/`, comandos de cada app.
- [ ] **C3.** Garantir que `docs/` permanece intocado.

---

## Validações

Rodar a cada iteração após mudanças:

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
npm run test
npm run build
```

### Geral
```bash
git status
```

---

## Critérios de Aceite (do PRD/Issue #1)

- [x] Backend roda local com `uvicorn src.main:app --reload` e responde `GET /health` com `{status, db, version}`.
- [x] Estrutura Deep Models criada (`api/routes`, `services`, `repositories`, `models`, `schemas`, `core`).
- [x] Pydantic `Settings` valida env e falha cedo.
- [x] Alembic init + revision vazia.
- [x] CORSMiddleware com allowlist.
- [x] Exception handler global retorna `{"error":{"code","message","field"}}`.
- [x] structlog JSON com request_id.
- [x] Sentry SDK inicializado (DSN opcional em dev).
- [x] Frontend roda com `npm run dev` e exibe placeholder.
- [x] Estrutura `src/{pages,features,components,hooks,stores,schemas,lib}` criada.
- [x] TanStack Query, Zustand, RR, Axios, RHF+Zod, shadcn/ui (Button, Dialog, Input, Toast), sonner instalados e providers globais.
- [x] `lib/format.ts` com `formatCurrency` e `formatDate` ptBR.
- [x] `.env.example` em ambos.
- [x] README curto.

---

## Notas Importantes

- **Sem integração Railway/Vercel ainda.** Tudo local. `DATABASE_URL` aponta para Postgres local (instalável via Docker ou nativo). Plano não exige Postgres rodando, mas health check deve degradar gracefulmente (`db: "error"`) sem travar boot.
- **Sem feature de domínio.** Não adicionar models, services, routes além de health. As issues seguintes (#2 auth, #3 cadastros, etc.) montam o domínio em cima desta base.
- **Migrations vazias** — primeira revision `0001_initial_empty.py` não cria tabela. Tabelas vêm com Issue #2 (tabela auth) e demais.
- **Mocks de DB nos testes** — `test_health` pode usar SQLite em memória ou mockar a sessão pra não exigir Postgres rodando em CI.
- **Toolchain Python** — usar `uv` se disponível; senão `pip install -e ".[dev]"`. Plano cobre ambos via `pyproject.toml`.
- **Toolchain Node** — `npm` é o default do plano. Se preferir `pnpm` ou `bun`, ajustar scripts.

---

## Tabela de Decisões

| Decisão | Valor | Origem |
|---------|-------|--------|
| Linguagem BE | Python 3.11+ | PRD §Stack BE |
| Framework BE | FastAPI | PRD §Stack BE |
| ORM | SQLAlchemy 2.0 | PRD §Stack BE |
| Migrations | Alembic | PRD §10.7.4 |
| Validação BE | Pydantic v2 + pydantic-settings | PRD §10.7.6 |
| Logging | structlog (JSON) | PRD §10.7.5 |
| Erros | Exception handler global, formato fixo | PRD §10.7.3 |
| Linguagem FE | TypeScript | PRD §Stack FE (implícito) |
| Build FE | Vite 5 | PRD §Stack FE |
| Estilo FE | TailwindCSS 3 | PRD §Stack FE |
| Estado FE | TanStack Query (server) + Zustand (UI) | PRD §Stack FE |
| Forms FE | RHF + Zod | PRD §Stack FE |
| UI base | shadcn/ui + sonner | PRD §10.6 |
| Datas | date-fns ptBR | PRD §10.6 |
| Erros FE | Sentry @sentry/react | PRD §10.7.5 |
| Testes BE | pytest + httpx | PRD §Testing |
| Testes FE | Vitest + RTL | PRD §Testing (futuro, smoke aqui) |
| Lint BE | ruff | Decisão de plano |
| Type check BE | mypy | Decisão de plano |
| Lint FE | ESLint | Decisão de plano |
| Type check FE | tsc --noEmit | Decisão de plano |

---

## Próximos passos pós-conclusão

Issue #2 (Auth) consome este foundation. Adiciona:
- Tabela `config_seguranca` (hash da senha) via migration `0002_auth.py`.
- Service `auth_service.py`, repository, schema, route `POST /api/auth/login`.
- FE: `<RequireAuth>`, página `/login`, layout pai com Topbar/Sidebar (vazia por enquanto).
