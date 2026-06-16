# PRP — Issue #14: Promoções schema + CRUD + UI
**GitHub Issue:** #14 | **Type:** HITL

## Contexto
- Última migration: `0058_create_tenant_eventos.py` → próxima será `0059`
- `tipo_recorrencia` ENUM novo no PG; no SQLite usar String com CHECK
- Conflito de promoções: resolver por `id ASC` (mais antiga vence) — documentar na UI
- Engine de aplicação no PDV vem no issue #17 — não implementar aqui

## Tarefas

### Bloco A — Migration
- [ ] A1. `0059_create_promocoes.py`: CREATE TYPE tipo_recorrencia AS ENUM ('nenhuma','semanal','mensal') (PG only)
- [ ] A2. CREATE TABLE promocoes (id BIGSERIAL PK, tenant_id BIGINT NOT NULL RLS, nome VARCHAR(100) NOT NULL, descricao TEXT, tipo_desconto VARCHAR(10) CHECK IN ('porcentagem','valor_fixo') NOT NULL, valor_desconto NUMERIC(10,2) NOT NULL, data_inicio DATE NOT NULL, data_fim DATE, hora_inicio TIME DEFAULT '00:00:00', hora_fim TIME DEFAULT '23:59:59', recorrencia tipo_recorrencia DEFAULT 'nenhuma', dias_semana INT[], dias_mes INT[], criado_por BIGINT FK system_users.id SET NULL, created_at TIMESTAMPTZ DEFAULT NOW())
- [ ] A3. CREATE TABLE promocao_produtos (promocao_id BIGINT FK promocoes.id CASCADE, produto_id BIGINT NOT NULL, PRIMARY KEY (promocao_id, produto_id)) — sem RLS (subordinada)
- [ ] A4. CREATE INDEX idx_promocoes_vigencia ON promocoes(tenant_id, data_inicio, data_fim)
- [ ] A5. RLS em promocoes (policy tenant_isolation)
- [ ] A6. INSERT template_permissions 'promocoes' screen para Admin e Gerente

### Bloco B — Model + Repository
- [ ] B1. `backend/src/models/promocoes.py`: Promocao + PromocaoProduto models (SQLAlchemy 2.0, mapped_column sem tipo em PKs)
- [ ] B2. `backend/src/repositories/promocoes_repository.py`: list_ativas(db, mes_ref), list_todas(db, status), create(db, data, produto_ids), update(db, id, data, produto_ids), delete(db, id), set_produtos(db, promocao_id, produto_ids)

### Bloco C — Schemas Pydantic
- [ ] C1. `backend/src/schemas/promocoes.py`: PromoçaoCreate com @model_validator:
  - recorrencia='nenhuma' → dias_semana e dias_mes devem ser None/vazios
  - recorrencia='semanal' → dias_semana obrigatório não-vazio, valores 0-6
  - recorrencia='mensal' → dias_mes obrigatório não-vazio, valores 1-31
  - data_fim >= data_inicio quando fornecido
- [ ] C2. PromoçaoUpdate (todos campos Optional exceto validações acima)
- [ ] C3. PromoçaoResponse com produto_ids: list[int]

### Bloco D — API Routes
- [ ] D1. `backend/src/api/routes/promocoes.py`: router com require_permission("cadastros")
- [ ] D2. GET /api/promocoes?status=ativas|futuras|todas (default: todas)
- [ ] D3. GET /api/promocoes/mes?mes=YYYY-MM (para calendário)
- [ ] D4. POST /api/promocoes (body PromoçaoCreate + produto_ids)
- [ ] D5. PATCH /api/promocoes/{id}
- [ ] D6. DELETE /api/promocoes/{id} → 204
- [ ] D7. Registrar router em `backend/src/main.py` prefix="/api/promocoes"

### Bloco E — Service Layer
- [ ] E1. `backend/src/services/promocoes_service.py`: wrappers thin sobre repository, raise HTTPException 404/422

### Bloco F — Frontend Hook
- [ ] F1. `frontend/src/features/cadastros/promocoes/usePromocoes.ts`:
  - interfaces: PromoçaoResponse, PromoçaoCreate, PromoçaoUpdate
  - usePromocoes(status?), useCreatePromocao(), useUpdatePromocao(), useDeletePromocao()
  - usePromocoesMes(mes: string) para calendário

### Bloco G — Frontend UI
- [ ] G1. `frontend/src/features/cadastros/promocoes/PromocoesPage.tsx`: listagem tabular com filtro status, botão "+ Promoção"
- [ ] G2. Modal criação/edição com campos: nome, descricao, tipo_desconto (select), valor_desconto, data_inicio, data_fim, hora_inicio, hora_fim, recorrencia (select), dias_semana (checkboxes 0-6, visível só se recorrencia=semanal), dias_mes (checkboxes 1-31, visível só se recorrencia=mensal), produto_ids (multiselect com busca)
- [ ] G3. Aviso inline no modal: "Produtos em múltiplas promoções ativas: aplica a mais antiga (menor ID)"
- [ ] G4. Integração calendário em `CalendarioPage.tsx`: camada verde para promoções vigentes no dia (sobreposta à camada azul de eventos)
- [ ] G5. Popover/tooltip ao clicar bloco verde: nome, vigência (data_inicio–data_fim), horário (hora_inicio–hora_fim), recorrência, produtos count
- [ ] G6. Rota `/cadastros/promocoes` no router + link no menu de cadastros

### Bloco H — Testes Backend
- [ ] H1. `backend/tests/test_promocoes.py`:
  - test_criar_promocao_semanal_valida: dias_semana=[1,3,5] OK
  - test_criar_promocao_semanal_sem_dias: 422
  - test_criar_promocao_nenhuma_com_dias: recorrencia=nenhuma + dias_semana preenchido → 422
  - test_crud_completo: create → list → update → delete
  - test_rls_cross_tenant: tenant A não vê promoções do tenant B
  - test_data_fim_antes_inicio: 422

## Validações
```bash
cd backend && python -m pytest tests/test_promocoes.py -v
cd frontend && npm run type-check && npm run lint && npm run build
```

## Definition of Done
- Migration 0059 aplica limpa (`alembic upgrade head`)
- pytest verde (sem quebrar testes existentes)
- frontend build verde, type-check e lint limpos
- CRUD funcional: criar, listar, editar, deletar promoção com produtos
- Calendário mostra camada verde nos dias de vigência com popover
- commit referenciando #14
