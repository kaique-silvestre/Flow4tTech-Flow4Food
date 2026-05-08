---
iteration: 4
max_iterations: 10
plan_path: "docs/issues/issues_matchpoint_v0.1.md"
started_at: "2026-05-08T00:00:00Z"
---

# Ralph Progress Log

## Codebase Patterns
- Backend: FastAPI + SQLAlchemy + Pydantic. Python 3.9 → `Optional[X]` não `X | None`.
- Todos routes usam `get_db` + `get_current_user` deps. Router registrado em `main.py`.
- Tests: engine SQLite em memória, fixture `c` (TestClient), helpers inline, `_setup_db` autouse.
- Singleton pattern: Estabelecimento e ConfigSeguranca usam id=1 / limit(1).
- `auth_service.py`: `hash_password`, `verify_password` já implementados — reusar.
- Import order ruff: alfabético. Novos routers inserir na ordem correta em main.py.
- ErrorCode.VALIDATION_ERROR existe em `src/core/errors.py`.
- Ruff UP035: usar `dict[x]`, `list[x]`, `tuple[x]` nativos. Não usar `Dict`, `List`, `Tuple` de `typing`.
- Frontend: React + TypeScript + Tailwind + React Router. `useNavigate` para navegação.
- `ComandaAbertaPage` tem dois branches: `status=fechada` (retorno antecipado ln 100) e `status=aberta` (retorno principal ln 154).
- `FechamentoPage` já tem `← Voltar` navegando para `/comandas/${id}` (volta à comanda, não à lista).
- Frontend tests: apenas `src/lib/format.test.ts` (unit). Sem component tests.
- Frontend: sem shadcn Tabs — implementar tabs manualmente com Tailwind + estado local.
- `DashboardPage.tsx` tem 8 erros TypeScript pré-existentes (recharts sem types) — não bloqueia issue 1.

## Iteration 1 - 2026-05-08T21:22:00Z

### Completed
- Adicionado `Button variant="outline" size="sm"` "← Voltar" no header de `ComandaAbertaPage`
- Botão navega para `/comandas` via `navigate("/comandas")`
- Botão está dentro do branch `status=aberta` (retorno principal) — não aparece em FechamentoPage
- Arquivo: `frontend/src/features/comandas/ComandaAbertaPage.tsx`
- Commit: de69360

### Validation Status
- type-check: FAIL (pré-existente — 8 erros em DashboardPage.tsx, não relacionados)
- lint: PASS
- tests: PASS (3/3)
- build: N/A (não executado — erros pré-existentes em type-check bloqueiam build)

### Learnings
- `npm run type-check` falha por erros pré-existentes em `DashboardPage.tsx` (recharts sem types)
- Esses erros existiam antes da minha mudança (confirmado via git stash test)

### Next Steps
- Issue 1 completa. Prosseguir para Issue 2 — M004: Helper formatQuantidade

---

## Iteration 2 - 2026-05-08T18:25:00Z

### Completed
- `formatQuantidade(value: number): string` adicionada em `frontend/src/lib/format.ts`
- Lógica: `Number.isInteger(value)` → `String(value)`; fracionário → `parseFloat(value.toFixed(3)).toString()`
- Aplicada em `ComandaAbertaPage.tsx` nas 3 ocorrências de `{ic.quantidade}` (fechada, ativa, cancelados)
- 5 testes de unidade adicionados em `format.test.ts`
- Commit: 5907525

### Validation Status
- lint: PASS
- tests: PASS (8/8 — 3 pre-existentes + 5 novos)
- type-check: FAIL (pré-existente — 8 erros em DashboardPage.tsx, recharts)

### Learnings
- `Number.isInteger(3.000)` = `true` em JS/TS (3.000 é 3 internamente)
- `parseFloat(n.toFixed(3))` efetivamente trunca a 3 casas e remove zeros à direita

### Next Steps
- Issue 2 completa. Próxima: Issue 3 — M015: NavLink prop `end` no Sidebar

---

## Iteration 3 - 2026-05-08T18:27:00Z

### Completed
- `end` prop adicionada a todos os `NavLink` em `Sidebar.tsx`
- Mudança: `end={item.to === "/"}` → `end` (linha 50)
- Arquivo: `frontend/src/components/layout/Sidebar.tsx`
- Commit: e73406d

### Validation Status
- lint: PASS
- tests: PASS (8/8)
- type-check: FAIL (pré-existente — DashboardPage.tsx recharts)

### Learnings
- `end` prop no NavLink força exact match — sem ela, `/estoque` fica ativo em `/estoque/movimentos`
- Sidebar já tinha `end={item.to === "/"}` como tentativa parcial — fix foi generalizar

### Next Steps
- Issue 3 completa. Todas as issues AFK sem blocker concluídas (1, 2, 3).
- Próximas issues sem blocker: 7 (M005), 8 (M006), 9 (M007), 10 (M008+M011), 12 (M010), 13 (M013), 14 (M014), 17 (M017)

---

## Iteration 4 - 2026-05-08T21:51:00Z

### Completed
- Todos os testes de integração migrados para nova arquitetura Insumo/Produto
- test_fechamento.py: `_criar_insumo` corrigido (sem circular import), testes de estoque reescritos usando ficha_tecnica + `insumo_id`
- test_comprovante.py: `_criar_item` → `/api/produtos`
- test_dashboard.py: `_criar_item` → `/api/produtos`, `_set_custo_medio` usa `Insumo`, `test_dashboard_lucro_estimado` usa insumo+ficha_tecnica
- test_reabertura.py: reescrito — usa `_criar_insumo` + `_criar_produto` + ficha_tecnica, `MovimentoEstoque.insumo_id`
- test_relatorios.py: `_criar_item` → `/api/produtos`
- test_relatorios_financeiros.py: `_criar_insumo` adicionado, `_set_custo_medio` usa `Insumo`, testes de CMV usam ficha_tecnica
- test_itens.py: reescrito — verifica que todos os endpoints `/api/itens` retornam 404
- comprovante_service.py: `_get_item_nome` usa `produtos_repository` + `ic.produto_id`
- Commit: 87e4861

### Validation Status
- lint: PASS (ruff — 0 errors)
- tests: PASS (95/95)

### Learnings
- CMV no DRE/dashboard vem de FichaTecnica→Insumo.custo_medio
- `baixa_sem_venda` aceita `item_id` no schema mas internamente busca insumo
- `comprovante_service._get_item_nome` usava `ic.item_id` — atualizado para `ic.produto_id`

### Next Steps
- Pendente: Alembic migrations (0009–0017)
- Pendente: Frontend — criar useInsumos.ts, useProdutos.ts, atualizar NovaCompraPage.tsx, ComandaAbertaPage.tsx, Sidebar.tsx, App.tsx
- Backend M000 100% completo e testado

---

## Iteration 5 - 2026-05-08T22:00:00Z

### Completed
- 9 Alembic migrations (0009–0017): criação de insumos/produtos/ficha_tecnica, migração de dados, rename de FKs, drop de tabelas antigas
- Frontend: useInsumos.ts, useProdutos.ts criados
- NovaCompraPage: useInsumos (era useItensSimples)
- ComandaAbertaPage: useProdutos (era useItens vendavel=true)
- useComandas.useTopItens: /api/produtos/top (era /api/itens/top)
- Sidebar: remove "Itens" do menu
- App.tsx: remove rota /cadastros/itens
- Commits: 87e4861 (backend), 662ffde (migrations+frontend)

### Validation Status
- Backend lint: PASS (ruff 0 errors)
- Backend tests: PASS (95/95)
- Frontend lint: PASS (eslint 0 warnings)
- Frontend tests: PASS (8/8)
- TypeScript: apenas erros pré-existentes em DashboardPage.tsx (recharts)

### M000 Status
COMPLETE — todos os critérios de aceite atendidos:
- ✅ Tabelas insumos, produtos, ficha_tecnica
- ✅ GET /api/insumos e GET /api/produtos
- ✅ GET /api/itens retorna 404
- ✅ NovaCompraPage usa GET /api/insumos
- ✅ ComandaAbertaPage usa GET /api/produtos
- ✅ Link "Itens" removido do Sidebar
- ✅ Fechar comanda desconta insumos via ficha_tecnica
- ✅ Migrations executam em sequência completa
- ✅ Cada migration é reversível individualmente

---
