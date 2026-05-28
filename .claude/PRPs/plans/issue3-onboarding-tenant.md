# PRP — Issue 3: Onboarding atômico de tenant

## Contexto
Issue 3 do projeto Flow4Tech. Bloqueada por Issues 1 e 2 (já completas).
Cria o fluxo de onboarding de novo tenant: transação única que cria tenant + perfis clonados + admin user + assinatura trial.

## Decisão HITL — Superadmin Auth
**Escolha: token estático via env var `SUPERADMIN_TOKEN`.**
Mecanismo: `Authorization: Bearer <SUPERADMIN_TOKEN>` nas rotas `/admin/`.
Simples, sem JWT extra. Issue 4 pode migrar para claim JWT se necessário.

## Arquivos a criar

### 1. Migration 0045_create_assinaturas.py
Tabela `assinaturas` mínima para Issue 3:
- id, tenant_id (FK tenants.id UNIQUE), status (trial/ativa/vencida/cancelada/suspensa), data_inicio, data_vencimento (nullable), created_at, updated_at

### 2. backend/src/models/assinaturas.py
SQLAlchemy model `Assinatura`.

### 3. backend/src/schemas/tenants.py
Pydantic schemas:
- `TenantCreate`: nome_fantasia (str, obrigatório), cnpj (str, opcional), admin_name (str), admin_username (str), admin_email (str — obrigatório no onboarding), admin_password (str)
- `TenantResponse`: id, nome_fantasia, cnpj, status, admin_user_id, created_at
- `TenantUpdate`: nome_fantasia (opcional), status (opcional)
- `TenantDetailResponse`: TenantResponse + assinatura_status

### 4. backend/src/repositories/tenant_repository.py
- `create_tenant(db, tenant) -> Tenant`
- `get_tenant_by_id(db, id) -> Optional[Tenant]`
- `update_tenant(db, tenant) -> Tenant`
- `list_tenants(db) -> list[Tenant]`
- `get_assinatura_by_tenant(db, tenant_id) -> Optional[Assinatura]`
- `create_assinatura(db, assinatura) -> Assinatura`

### 5. backend/src/services/tenant_service.py
- `criar_tenant(db, data: TenantCreate) -> TenantDetailResponse`
  - Transação única:
    1. INSERT tenants
    2. Clone profiles de tenant_id=1 (Admin, Gerente, Caixa) para novo tenant_id
    3. Clone profile_permissions de cada perfil clonado
    4. CREATE SystemUser admin com email obrigatório
    5. INSERT assinaturas status='trial', data_inicio=now()
    6. UPDATE tenants.admin_user_id
    7. db.commit()
  - Rollback automático em qualquer falha (usa db.rollback() ou single commit)
- `get_tenant(db, id) -> TenantDetailResponse`
- `update_tenant(db, id, data: TenantUpdate) -> TenantDetailResponse`

### 6. backend/src/api/routes/admin.py
Router `/admin/tenants`:
- `POST /admin/tenants` → `criar_tenant`
- `GET /admin/tenants/{id}` → `get_tenant`
- `PATCH /admin/tenants/{id}` → `update_tenant`

Dependency `require_superadmin`:
- Lê `Authorization: Bearer <token>` header
- Compara com `settings.SUPERADMIN_TOKEN`
- 403 se não bater

### 7. backend/src/core/config.py (modificar)
Adicionar: `SUPERADMIN_TOKEN: str = Field("", description="Static token for superadmin /admin/ routes")`

### 8. backend/src/main.py (modificar)
Registrar: `app.include_router(admin_routes.router, prefix="/api/admin", tags=["admin"])`

### 9. backend/tests/test_issue3_onboarding.py
Testes (SQLite in-memory, FakeSession pattern do conftest):
- `test_post_admin_tenants_creates_tenant` — 201, retorna id
- `test_post_admin_tenants_requires_superadmin` — sem token → 403
- `test_post_admin_tenants_wrong_token` — token errado → 403
- `test_get_admin_tenant_returns_assinatura` — retorna status trial
- `test_patch_admin_tenant_updates_fields` — atualiza nome_fantasia
- `test_patch_admin_tenant_forbidden_non_superadmin` — 403
- `test_atomic_rollback_on_duplicate_email` — email duplicado → rollback (no tenant orphan)
- `test_get_tenant_not_found` — 404

## Validações pós-implementação
```bash
cd backend
source .venv/bin/activate
python -m pytest tests/test_issue3_onboarding.py -v
python -m ruff check src/
python -m mypy src/ --ignore-missing-imports
```

## Checklist acceptance criteria (Issue 3)
- [ ] POST /admin/tenants: tenant + perfis clonados + usuário admin + assinatura trial em transação única
- [ ] Falha em qualquer passo → rollback completo (sem órfão)
- [ ] tenant.admin_user_id preenchido após criação
- [ ] Email do usuário admin obrigatório no onboarding
- [ ] Perfis clonados têm tenant_id do novo tenant
- [ ] GET /admin/tenants/{id} retorna dados + status assinatura
- [ ] PATCH /admin/tenants/{id} permite atualizar nome_fantasia e status
- [ ] Rotas /admin/ retornam 403 para não-superadmin
- [ ] Teste de transação atômica
