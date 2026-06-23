# PRP — Issue #12: Platform admin auth + BYPASSRLS
**GitHub Issue:** #12 | **Type:** HITL

## Contexto
- Last migration: `0056_permission_templates.py` (down_revision: "0055")
- Stack: FastAPI + SQLAlchemy 2.0 + PyJWT (`import jwt`) + bcrypt (`import bcrypt` direto)
- DB: PostgreSQL com RLS; SQLite in-memory nos testes
- `admin.py` existente com `require_superadmin` via SUPERADMIN_TOKEN — NÃO remover
- Padrão engine: `create_engine(DATABASE_URL, pool_pre_ping=True, future=True, connect_args={"options": "-c timezone=UTC"})`
- `require_permission` em `dependencies.py` como modelo para `require_platform_admin`
- Platform engine: sem RLS, sem checkout listener de tenant, pool separado
- JWT: mesmo `JWT_SECRET`, payload com `platform_admin=True`, sem `tenant_id`
- Security: rejeitar token de tenant em `/api/platform/*` — checar ausência de `tenant_id` E presença de `platform_admin=True`

## Tarefas

### Bloco A — Migration
- [ ] A1. Migration `0057_create_platform_admins.py`:
       CREATE TABLE platform_admins
       (id BIGSERIAL PK, email VARCHAR(254) UNIQUE NOT NULL,
        name VARCHAR(200) NOT NULL, password_hash VARCHAR(200) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMPTZ DEFAULT NOW())
- [ ] A2. Sem tenant_id — tabela global, sem RLS

### Bloco B — Settings + Engine
- [ ] B1. Adicionar `DATABASE_URL_PLATFORM: str = ""` em `Settings` (config.py)
- [ ] B2. Criar `platform_engine` e `PlatformSessionLocal` em `database.py`
       (fallback para `DATABASE_URL` se `DATABASE_URL_PLATFORM` vazio — dev only)
       Sem checkout listener de tenant neste engine
- [ ] B3. Criar `get_platform_db()` generator em `database.py`

### Bloco C — Model + Repository
- [ ] C1. `backend/src/models/platform_admin.py`: PlatformAdmin model (sem tenant_id, sem RLS)
       Campos: id, email, name, password_hash, is_active, created_at
- [ ] C2. `backend/src/repositories/platform_admins_repository.py`:
       `get_by_email(db, email)`, `create(db, email, name, password_hash)`

### Bloco D — Service + Auth
- [ ] D1. `backend/src/services/platform_auth_service.py`:
       `login(db, email, password) → {"access_token": str}`
       Verifica is_active, verifica senha com `bcrypt.checkpw`, retorna token
- [ ] D2. `create_platform_token(platform_admin_id, email)`:
       payload: `{"sub": str(id), "platform_admin_id": id, "platform_admin": True, "email": email}`
       Sem `tenant_id` no payload. Usa `create_access_token` de `auth_service.py`

### Bloco E — Dependency + Middleware
- [ ] E1. `require_platform_admin` em `dependencies.py`:
       Decodifica JWT, verifica `platform_admin=True`
       Rejeita com 403 se: `platform_admin` ausente/False, `tenant_id` presente no payload, token inválido
       Rejeita com 401 se token ausente
- [ ] E2. Aplicar como `dependencies=[Depends(require_platform_admin)]` no APIRouter de plataforma
       (NÃO dentro de endpoints individuais)

### Bloco F — Routes
- [ ] F1. `backend/src/api/routes/platform_auth.py`:
       POST `/api/platform/auth/login` → body `{email, password}` → `{access_token}`
       Router com `dependencies=[Depends(require_platform_admin)]` EXCETO login (sem dep)
       Login é público — não precisa de auth
- [ ] F2. Registrar em `main.py`:
       `app.include_router(platform_auth_routes.router, prefix="/api/platform", tags=["platform"])`

### Bloco G — Testes
- [ ] G1. `backend/tests/test_platform_auth.py`:
       Login válido → JWT com `platform_admin=True`
- [ ] G2. JWT de tenant (com `tenant_id`) rejeitado em rota protegida com 403
- [ ] G3. Request sem token → 401
- [ ] G4. Senha errada → 401
- [ ] G5. Admin inativo → 401

## Notas SQLite (testes)
- PlatformAdmin model: `id: Mapped[int] = mapped_column(primary_key=True)` (sem BigInteger)
- `created_at`: passar explícito nos fixtures (sem `server_default NOW()`)
- `get_platform_db` nos testes deve usar a mesma `TestSessionLocal` do conftest.py — usar override

## Validações
```bash
cd backend && python -m pytest
```
