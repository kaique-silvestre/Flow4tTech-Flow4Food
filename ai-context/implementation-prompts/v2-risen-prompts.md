# RISEN Prompts — Flow4Food V2 (Issues #10–#19)

> Cole o prompt de cada issue em uma instância separada do Claude Code no diretório raiz do projeto.
> Cada prompt é autossuficiente: lê o contexto, cria o plano PRP e executa com `/prp-ralph-loop`.

---

## Contexto comum (lido automaticamente por cada prompt)

**Stack:**
- Backend: FastAPI + SQLAlchemy 2.0 + Alembic + PyJWT (`import jwt`) + bcrypt (`import bcrypt` direto)
- Frontend: React + TypeScript + Vite + Zustand + React Query + Zod
- DB: PostgreSQL com RLS via `SET app.tenant_id`; SQLite em memória nos testes
- Migrations: `backend/alembic/versions/` — numeradas sequencialmente (última: `0055_`)
- Testes: `pytest` com SQLite in-memory via `conftest.py`

**Gotchas globais:**
- NUNCA usar `passlib` — `import bcrypt` direto
- NUNCA usar `jose` — `import jwt` (PyJWT)
- SQLite testes: PKs como `mapped_column(primary_key=True)` sem tipo; `created_at` explícito nos fixtures (sem `server_default NOW()`)
- Toda tabela nova com RLS precisa de `tenant_id` com `server_default=sa.text("(NULLIF(current_setting('app.tenant_id', true), ''))::bigint")`
- `conftest.py` já patcha `tenant_id` para SQLite — não duplicar

**Validações:**
```bash
cd backend && python -m pytest
cd frontend && npm run type-check && npm run lint && npm run build
```



**GitHub:** #15 | **Bloqueadores:** #11 | **Tipo:** AFK

### Role
Engenheiro backend no Flow4Food. Atualize a lógica de mint do JWT para que perfis com `template_id` leiam permissões de `template_permissions` — sem copiar para `profile_permissions`. Mudança cirúrgica em `auth_service.py`.

### Instructions
`profile_permissions` continua sendo usado para perfis custom (`template_id IS NULL`). O comportamento V1 deve ser preservado nesses casos.

### Steps

**1. Leia:**
- `backend/src/services/auth_service.py` — `_build_token_response` e `rotate_refresh_token` (onde permissões são montadas)
- `backend/src/models/profiles.py` — Profile com o novo `template_id` e relationship `template`
- `backend/src/repositories/profiles_repository.py`
- `backend/tests/test_auth.py` — padrão de testes de auth

**2. Crie o PRP** em `.claude/PRPs/plans/issue-15-resolucao-permissao-template.md`:
```markdown
# PRP — Issue #15: Resolução de permissão via template
**GitHub Issue:** #15 | **Type:** AFK | **Depende de:** #11

## Tarefas
- [ ] A1. Criar helper resolve_permissions(user) → list[str]:
           SE profile.template_id IS NOT NULL → ler de template_permissions
           SE profile.template_id IS NULL → ler de profile_permissions
           SE profile_id IS NULL (usuário livre) → ler de user_permissions (placeholder para #18)
- [ ] A2. Substituir [p.screen for p in user.profile.permissions if p.can_access]
           por resolve_permissions(user) em _build_token_response
- [ ] A3. Mesmo em rotate_refresh_token
- [ ] B1. Teste: login com perfil template_id SET → JWT contém telas do template
- [ ] B2. Teste: login com perfil template_id NULL → JWT contém telas de profile_permissions
- [ ] B3. Teste: atualizar template_permissions → rotate_refresh_token emite telas atualizadas

## Validações
- pytest backend
```

**3. Execute:**
```
/prp-ralph-loop .claude/PRPs/plans/issue-15-resolucao-permissao-template.md --max-iterations 6
```

### End Goal
- `resolve_permissions()` centraliza lógica para todos os casos
- Testes cobrindo template vs custom vs futuro usuário livre
- pytest verde, commit #15

---

## Issue #16 — [2B] Painel admin: listagem de tenants e gestão de assinaturas

**GitHub:** #16 | **Bloqueadores:** #12 | **Tipo:** AFK

### Role
Engenheiro full-stack no Flow4Food. Implemente os endpoints e UI do painel da Flow4Tech: listar tenants, ver usuários por empresa, ativar/suspender assinaturas. Usa exclusivamente o engine BYPASSRLS do issue #12.

### Instructions
Todas as queries usam `get_platform_db()` — nunca `get_tenant_db()`. O painel não tem RLS por design.

### Steps

**1. Leia:**
- `backend/src/models/tenants.py` — Tenant (nome_fantasia, cnpj, status)
- `backend/src/models/assinaturas.py` — Assinatura (status: trial|ativa|suspensa|cancelada)
- `backend/src/models/system_users.py` — SystemUser
- `backend/src/core/database.py` — `get_platform_db()` criado no #12
- `backend/src/api/dependencies.py` — `require_platform_admin` criado no #12
- `backend/src/api/routes/admin.py` — padrão de rota admin existente

**2. Crie o PRP** em `.claude/PRPs/plans/issue-16-painel-admin-tenants.md`:
```markdown
# PRP — Issue #16: Painel admin tenants + assinaturas
**GitHub Issue:** #16 | **Type:** AFK | **Depende de:** #12

## Tarefas

### Bloco A — Repository
- [ ] A1. platform_repository.py: list_tenants(db, status_filter?) com join em assinaturas
- [ ] A2. get_tenant_users(db, tenant_id) → list de usuários com perfil e last_login
- [ ] A3. update_assinatura_status(db, tenant_id, status)

### Bloco B — API
- [ ] B1. GET /api/platform/tenants?status= → lista com nome_fantasia, cnpj, status assinatura, data_vencimento
- [ ] B2. GET /api/platform/tenants/{id}/users → usuários com nome, username, perfil, last_login
- [ ] B3. PATCH /api/platform/tenants/{id}/assinatura → {status: "ativa"|"suspensa"}
- [ ] B4. Todos os endpoints com Depends(require_platform_admin) + get_platform_db

### Bloco C — Frontend (painel separado)
- [ ] C1. Rota /platform com layout próprio (sem sidebar de tenant)
- [ ] C2. PlatformLoginPage → /platform/login
- [ ] C3. PlatformTenantsPage → tabela com filtro por status + ações de suspender/ativar
- [ ] C4. PlatformTenantDetailPage → usuários do tenant
- [ ] C5. authStore separado para platform (platformAuthStore)
- [ ] C6. Guard RequirePlatformAuth

### Bloco D — Testes
- [ ] D1. GET /platform/tenants retorna dados de múltiplos tenants
- [ ] D2. PATCH assinatura atualiza status
- [ ] D3. JWT de tenant rejeitado nos endpoints de plataforma

## Validações
- pytest backend
- npm run type-check && npm run lint && npm run build
```

**3. Execute:**
```
/prp-ralph-loop .claude/PRPs/plans/issue-16-painel-admin-tenants.md --max-iterations 10
```

### End Goal
- Endpoints de listagem e gestão funcionando com BYPASSRLS
- UI de painel separado com login próprio
- pytest + frontend build verdes, commit #16

---

## Issue #17 — [3YB] Engine de desconto no PDV

**GitHub:** #17 | **Bloqueadores:** #14 | **Tipo:** AFK

### Role
Engenheiro backend no Flow4Food. Implemente a validação de promoções ativas ao lançar um item na comanda. Lógica de matching: data, horário e recorrência. Conflito resolve por `id ASC`.

### Instructions
Mudança cirúrgica no serviço/rota de lançamento de item na comanda. O item da comanda deve registrar qual `promocao_id` foi aplicado. Frontend só exibe — não calcula desconto.

### Steps

**1. Leia:**
- `backend/src/models/itens_comanda.py` — ItemComanda (campos atuais)
- `backend/src/models/comandas.py` — Comanda
- `backend/src/api/routes/comandas.py` — rota de lançamento de item
- `backend/src/services/` — se existe service de comanda
- `backend/src/models/` — Promocao e PromoçaoProduto criados no #14
- `backend/tests/test_comandas.py` — padrão de teste de comanda

**2. Crie o PRP** em `.claude/PRPs/plans/issue-17-engine-desconto.md`:
```markdown
# PRP — Issue #17: Engine de desconto no PDV
**GitHub Issue:** #17 | **Type:** AFK | **Depende de:** #14

## Tarefas

### Bloco A — Migration
- [ ] A1. ALTER TABLE itens_comanda ADD COLUMN promocao_id BIGINT REFERENCES promocoes(id) NULL
- [ ] A2. ALTER TABLE itens_comanda ADD COLUMN preco_original NUMERIC(10,2) NULL
           (salvar preço antes do desconto para auditoria)

### Bloco B — Lógica de matching
- [ ] B1. promocoes_service.find_active_promo(db, tenant_id, produto_id, now) → Promocao | None:
           WHERE data_inicio <= hoje AND (data_fim IS NULL OR data_fim >= hoje)
           AND hora_inicio <= hora_atual AND hora_fim >= hora_atual
           AND produto_id IN promocao_produtos
           + filtro de recorrência em Python (dias_semana/dias_mes)
           ORDER BY id ASC LIMIT 1
- [ ] B2. Aplicar desconto: porcentagem ou valor_fixo sobre preco_venda do produto

### Bloco C — Integração na comanda
- [ ] C1. No endpoint/service de lançar item: chamar find_active_promo após resolver produto
- [ ] C2. Se promo ativa: salvar preco_original, calcular preco_com_desconto, salvar promocao_id
- [ ] C3. Response do item de comanda incluir: preco_original, desconto_aplicado, promocao_nome

### Bloco D — Testes
- [ ] D1. Lançar item com promo ativa → preço com desconto correto + promocao_id salvo
- [ ] D2. Lançar item fora do horário de promo → sem desconto
- [ ] D3. Lançar item com recorrência semanal no dia errado → sem desconto
- [ ] D4. Duas promos para mesmo produto → aplica a de menor id

## Validações
- pytest backend
```

**3. Execute:**
```
/prp-ralph-loop .claude/PRPs/plans/issue-17-engine-desconto.md --max-iterations 8
```

### End Goal
- Desconto aplicado automaticamente ao lançar item com promo ativa
- `promocao_id` e `preco_original` salvos no item da comanda
- Todos os cenários de matching testados
- pytest verde, commit #17

---

## Issue #18 — [1D] Usuário livre: profile_id nullable e user_permissions

**GitHub:** #18 | **Bloqueadores:** #15 | **Tipo:** AFK

### Role
Engenheiro full-stack no Flow4Food. Torne `profile_id` nullable em `system_users` e implemente `user_permissions` para usuários sem perfil fixo. Mudança de schema + auth + UI de criação de usuário.

### Instructions
Rows existentes: zero impacto (todos têm `profile_id`). Usuário livre com `user_permissions` vazio recebe `permissions = []` no JWT — deny-by-default.

### Steps

**1. Leia:**
- `backend/src/models/system_users.py` — SystemUser com profile_id NOT NULL atual
- `backend/src/services/auth_service.py` — resolve_permissions (criado no #15)
- `backend/src/api/routes/users.py` — rota de criação de usuário
- `frontend/src/features/configuracoes/` — UI de criação de usuário
- `backend/alembic/versions/0055_*.py` — padrão de migration

**2. Crie o PRP** em `.claude/PRPs/plans/issue-18-usuario-livre.md`:
```markdown
# PRP — Issue #18: Usuário livre
**GitHub Issue:** #18 | **Type:** AFK | **Depende de:** #15

## Tarefas

### Bloco A — Migration
- [ ] A1. CREATE TABLE user_permissions (id BIGSERIAL PK, tenant_id BIGINT,
           user_id BIGINT REFERENCES system_users(id) ON DELETE CASCADE,
           screen VARCHAR(50), can_access BOOLEAN, UNIQUE(user_id, screen))
- [ ] A2. ALTER TABLE system_users ALTER COLUMN profile_id DROP NOT NULL
- [ ] A3. RLS em user_permissions

### Bloco B — Model + Repository
- [ ] B1. UserPermission model
- [ ] B2. user_permissions_repository: list_by_user, upsert, delete

### Bloco C — Auth Update
- [ ] C1. Atualizar resolve_permissions(user): SE profile_id IS NULL → ler de user_permissions
           SE user_permissions vazio → retornar [] (deny-by-default)

### Bloco D — API
- [ ] D1. GET /api/users/{id}/permissions → list de screens do usuário livre
- [ ] D2. PUT /api/users/{id}/permissions → {screens: list[str]} — substituição completa
- [ ] D3. Atualizar POST /api/users para aceitar profile_id opcional (null = usuário livre)

### Bloco E — Frontend
- [ ] E1. Campo "Perfil" opcional no formulário de criação de usuário
- [ ] E2. Se perfil vazio: mostrar checkboxes de telas diretamente
- [ ] E3. Se perfil preenchido: comportamento atual (sem checkboxes extras)

### Bloco F — Testes
- [ ] F1. Criar usuário com profile_id=None → JWT com telas de user_permissions
- [ ] F2. Usuário livre sem user_permissions → JWT com permissions=[]
- [ ] F3. Usuário com profile_id continua funcionando igual

## Validações
- pytest backend
- npm run type-check && npm run lint && npm run build
```

**3. Execute:**
```
/prp-ralph-loop .claude/PRPs/plans/issue-18-usuario-livre.md --max-iterations 8
```

### End Goal
- `profile_id` nullable sem quebrar usuários existentes
- `user_permissions` funcionando com deny-by-default
- UI de criação com campo de perfil opcional
- pytest + frontend build verdes, commit #18

---

## Issue #19 — [3ZA] Cockpit consolidado: view SQL, UI em camadas, filtros e deep links

**GitHub:** #19 | **Bloqueadores:** #13, #14 | **Tipo:** HITL

### Role
Engenheiro full-stack no Flow4Food. Implemente o cockpit de gestão: view SQL unindo 4 camadas, endpoint com filtro por permissão do usuário, e UI com toggles de camada e deep links.

### Instructions
A view SQL usa nomes REAIS do codebase — os nomes do esboço original estavam errados. Veja o mapeamento correto abaixo. Omissão de camadas por permissão acontece na API, não no frontend.

### Steps

**1. Leia:**
- `backend/src/models/contas_pagar.py` — ContaPagar (tabela: `contas_pagar`, status: `pendente`)
- `backend/src/models/compras.py` — Compra (tabela: `compras`, status: `confirmado`, campo: `data_prevista_recebimento`)
- `backend/src/models/fornecedores.py` — Fornecedor (campo: `nome`)
- `backend/src/models/` — TenantEvento (#13) e Promocao (#14)
- `backend/src/api/dependencies.py` — `require_permission` para filtrar camadas
- `frontend/src/features/` — padrão de feature com múltiplos tipos de dado

**2. Mapeamento correto (erros do esboço original):**
```
ERRADO → CORRETO
financeiro_contas_pagar → contas_pagar
fornecedor_nome (string) → JOIN fornecedores ON id = fornecedor_id → fornecedores.nome
compras_pedidos → compras
status = 'aguardando_entrega' → status = 'confirmado' (pedido feito, não recebido)
data_entrega_prevista → data_prevista_recebimento
hora_entrega_prevista → não existe → usar '08:00:00'::TIME como placeholder
```

**3. Crie o PRP** em `.claude/PRPs/plans/issue-19-cockpit-consolidado.md`:
```markdown
# PRP — Issue #19: Cockpit consolidado
**GitHub Issue:** #19 | **Type:** HITL | **Depende de:** #13, #14

## Tarefas

### Bloco A — View SQL
- [ ] A1. Criar migration com CREATE OR REPLACE VIEW view_calendario_consolidado:
           UNION ALL de 4 camadas:
           1. tenant_eventos → tipo 'evento'
           2. promocoes (data_fim IS NULL OR data_fim >= CURRENT_DATE) → tipo 'promocao'
           3. contas_pagar LEFT JOIN fornecedores WHERE status='pendente' → tipo 'conta_pagar'
           4. compras LEFT JOIN fornecedores WHERE status='confirmado'
              AND data_prevista_recebimento IS NOT NULL → tipo 'entrega_insumo'
           Colunas: (tenant_id, data_referencia DATE, tipo, referencia_id, descricao, hora_inicio TIME)

### Bloco B — API
- [ ] B1. GET /api/calendario/consolidado?mes=YYYY-MM
           → filtrar por tenant_id do JWT
           → omitir 'conta_pagar' se tela "financeiro" ausente no JWT
           → omitir 'entrega_insumo' se tela "estoque" ausente no JWT
           → sempre incluir 'evento' e 'promocao' se tela "calendario" presente

### Bloco C — Frontend
- [ ] C1. Integrar camadas extras no CalendarioPage existente (#13)
- [ ] C2. Código de cores: azul=evento, verde=promoção, vermelho=conta_pagar, amarelo=entrega
- [ ] C3. Toggles de filtro por camada (4 checkboxes)
- [ ] C4. Modal ao clicar em conta_pagar: valor + botão "Ir para o Financeiro"
- [ ] C5. Modal ao clicar em entrega: insumos esperados + botão "Dar Entrada no Estoque"
- [ ] C6. Camadas ausentes do JWT simplesmente não renderizam (frontend recebe lista vazia delas)

### Bloco D — Testes
- [ ] D1. Usuário sem tela "financeiro" → resposta não contém items tipo 'conta_pagar'
- [ ] D2. Usuário com todas as telas → todas as 4 camadas presentes
- [ ] D3. Dados de tenant A não aparecem para tenant B

## Validações
- pytest backend
- npm run type-check && npm run lint && npm run build
```

**4. Execute:**
```
/prp-ralph-loop .claude/PRPs/plans/issue-19-cockpit-consolidado.md --max-iterations 12
```

### End Goal
- View SQL com nomes corretos de tabelas/colunas
- Endpoint filtra camadas por permissão do JWT
- UI com 4 camadas + toggles + deep links
- pytest + frontend build verdes, commit #19

s NFs 