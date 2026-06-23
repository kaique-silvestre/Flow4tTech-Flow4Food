# PRP — Issue #13: Calendário de eventos
**GitHub Issue:** #13 | **Type:** HITL

## Contexto
- Last migration após #12: `0057_create_platform_admins.py` (se #12 executar antes); caso contrário `0056`
- Stack: FastAPI + SQLAlchemy 2.0; React + TypeScript + Vite + Zustand + React Query + Zod
- Padrão de rota: `router = APIRouter(dependencies=[Depends(require_permission("calendario"))])`
- `get_tenant_db` para sessions com RLS; tenant_id via `server_default=sa.text("(NULLIF(current_setting('app.tenant_id', true), ''))::bigint")`
- Frontend padrão: feature dir com `Page.tsx` + `useX.ts` (React Query hooks)
- `data_evento` é DATE sem timezone — data local do estabelecimento
- Tela `"calendario"` adicionada nos templates Admin e Gerente via migration seed

## Tarefas

### Bloco A — Migration
- [ ] A1. Migration `0058_create_tenant_eventos.py` (ajustar número se necessário):
       CREATE TABLE tenant_eventos (
         id BIGSERIAL PK,
         tenant_id BIGINT NOT NULL,
         titulo VARCHAR(100) NOT NULL,
         descricao TEXT,
         data_evento DATE NOT NULL,
         criado_por BIGINT REFERENCES system_users(id) ON DELETE SET NULL,
         created_at TIMESTAMPTZ DEFAULT NOW(),
         updated_at TIMESTAMPTZ DEFAULT NOW()
       )
- [ ] A2. CREATE INDEX idx_tenant_eventos_data ON tenant_eventos(tenant_id, data_evento)
- [ ] A3. Habilitar RLS: `ALTER TABLE tenant_eventos ENABLE ROW LEVEL SECURITY`
       Policy: `CREATE POLICY tenant_isolation ON tenant_eventos USING (tenant_id = (NULLIF(current_setting('app.tenant_id', true), ''))::bigint)`
- [ ] A4. Seed tela "calendario" para templates Admin e Gerente (is_system=true):
       INSERT INTO template_permissions (template_id, screen, can_access)
       SELECT id, 'calendario', true FROM permission_templates WHERE is_system=true AND nome IN ('Admin', 'Gerente')
       ON CONFLICT DO NOTHING

### Bloco B — Model + Repository
- [ ] B1. `backend/src/models/eventos.py`: TenantEvento SQLAlchemy model
       Campos: id (mapped_column PK), tenant_id (BigInteger + server_default RLS), titulo, descricao, data_evento (Date), criado_por (FK nullable), created_at, updated_at
- [ ] B2. `backend/src/repositories/eventos_repository.py`:
       `list_by_month(db, year, month) → list[TenantEvento]`
       `create(db, data) → TenantEvento`
       `get_by_id(db, evento_id) → TenantEvento | None`
       `update(db, evento_id, data) → TenantEvento`
       `delete(db, evento_id) → None`

### Bloco C — API
- [ ] C1. `backend/src/schemas/eventos.py`:
       `EventoCreate`: titulo, descricao (opt), data_evento (date)
       `EventoPatch`: titulo (opt), descricao (opt)
       `EventoResponse`: id, tenant_id, titulo, descricao, data_evento, criado_por, created_at
- [ ] C2. `backend/src/services/eventos_service.py`:
       `list_by_month`, `criar_evento`, `patch_evento`, `delete_evento`
       `delete_evento` raises 404 if not found
- [ ] C3. `backend/src/api/routes/eventos.py`:
       Router com `dependencies=[Depends(require_permission("calendario"))]`
       GET `/api/eventos?mes=YYYY-MM` (default: mês atual, formato `datetime.now().strftime("%Y-%m")`)
       POST `/api/eventos` → 201
       PATCH `/api/eventos/{id}`
       DELETE `/api/eventos/{id}` → 204
- [ ] C4. Registrar em `main.py`:
       `app.include_router(eventos_routes.router, prefix="/api/eventos", tags=["eventos"])`

### Bloco D — Frontend
- [ ] D1. `frontend/src/features/calendario/useEventos.ts`:
       `useEventos(mes: string)` — GET `/api/eventos?mes={mes}`
       `useCreateEvento()` — POST
       `usePatchEvento()` — PATCH
       `useDeleteEvento()` — DELETE
       Query key: `["eventos", mes]`
- [ ] D2. `frontend/src/features/calendario/CalendarioPage.tsx`:
       Grid mensal: 7 colunas × semanas (domingo a sábado)
       Navegação prev/next mês com state `mesAtual` (formato YYYY-MM)
       Exibir título do evento nas células do dia
       Botão "+" no header → abre modal com data vazia
       Clique na célula do dia → abre modal com data pré-preenchida e travada
       Inline delete nos eventos do dia (botão × ao hover)
       Inline edit: clique no evento → abre modal preenchido
- [ ] D3. Modal de criação/edição:
       Campo titulo (required), descricao (textarea opcional), data_evento (date input)
       Quando data vem de clique na célula: input desabilitado
       Quando vem do botão "+": input habilitado, vazio
- [ ] D4. Tipos TypeScript: `EventoResponse`, `EventoCreate`, `EventoPatch`
- [ ] D5. Rota `/calendario` em `App.tsx` com guard de permissão (`"calendario"`)
       Adicionar item no menu lateral se existir componente de nav

### Bloco E — Testes
- [ ] E1. `backend/tests/test_eventos.py`:
       CRUD completo via API (create, list_by_month, patch, delete)
- [ ] E2. GET por mês retorna só eventos do mês correto (não meses adjacentes)
- [ ] E3. Evento de tenant A não aparece para tenant B (RLS isolation test)

## Notas SQLite (testes)
- TenantEvento model: `id: Mapped[int] = mapped_column(primary_key=True)` sem BigInteger
- `created_at` e `updated_at`: passar explícito nos fixtures
- RLS policies ignoradas no SQLite — testar isolamento via tenant_id nos dados

## Validações
```bash
cd backend && python -m pytest
cd frontend && npm run type-check && npm run lint && npm run build
```
