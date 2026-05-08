---
iteration: 4
max_iterations: 10
plan_path: ".claude/PRPs/plans/issue-14-ux-sweep.md"
started_at: "2026-05-08T18:00:00Z"
---

## Iteration 4 - 2026-05-08T23:10:00Z — Issue 5 (M001) IMPLEMENTADA

### Completed
- Backend: `FichaTecnicaItemResponse` + `custo_medio_insumo`; `delete_produto` → 422 se tem histórico; `desativar_produto` service + `PATCH /:id/desativar` route
- Backend: `tests/test_produtos.py` (9 testes, todos passando)
- Frontend: `useProdutos.ts` atualizado (FichaTecnicaItem, mutations create/update/desativar/delete)
- Frontend: `src/features/cardapio/` criado: `produtoSchemas.ts`, `ProdutoModal.tsx`, `CardapioPage.tsx`
- Frontend: `App.tsx` + `Sidebar.tsx` — rota `/cardapio` + NavLink "Cardápio"
- 104 testes backend passando, TypeScript zero erros

### Validation Status
- type-check: PASS (tsc --noEmit zero erros)
- lint: N/A
- Tests: PASS (104 backend — 9 novos test_produtos)
- Build: N/A

### Learnings
- `UnidadeBase` enum só aceita `"un"` e `"g"` — nunca "kg" em testes
- `ItemComanda` não tem campo `version` — não incluir em inserts diretos
- `Comanda.garcom_id` NOT NULL — usar garcom_id=1 em inserções de teste sem FK constraint SQLite
- `delete_produto` original fazia soft-delete silencioso; novo comportamento: 422 explícito com mensagem clara

---

## Iteration 3 - 2026-05-08T22:35:00Z — Issue 4 (M000) sincronizada

### Completed
- Verificou Issue 4 (M000) já implementada: commits 87e4861 + 662ffde + 92280a3
- Migrations 0009–0017 presentes (9 steps M000)
- 95 testes backend passando, TypeScript sem erros
- Marcou todos 14 critérios de aceite como `[x]` em docs/issues/issues_matchpoint_v0.1.md

### Validation Status
- type-check: PASS (tsc --noEmit zero erros)
- lint: N/A
- Tests: PASS (95 backend, 11 produto/insumo/compra)
- Build: N/A

### Learnings
- `ItensPage.tsx` + `ItemModal.tsx` ainda existem como dead code mas sem rota — não quebram nada
- `custo_medio` implementado em `src/services/compras_service.py:_calcular_custo_medio` com média ponderada
- `/api/itens` retorna 404 via `src/api/routes/itens.py` stub

---

## Iteration 2 - 2026-05-08T19:10:00Z — Issues 1, 2, 3 (matchpoint v0.1) sincronizadas

### Completed
- Verificou Issues 1 (M003), 2 (M004), 3 (M015) já implementadas em commits anteriores
- Marcou todos critérios de aceite como concluídos em docs/issues/issues_matchpoint_v0.1.md
- Tests: 8/8 passando (`formatQuantidade` + `formatCurrency` + `formatDate`)

### Validation Status
- type-check: N/A (só docs)
- lint: N/A
- Tests: PASS (8 testes)
- Build: N/A

### Learnings
- Issues matchpoint v0.1 foram implementadas antes de docs serem criados — sempre checar git log antes de implementar
- `format.ts` já tem `formatQuantidade` com lógica correta: `Number.isInteger` + `parseFloat(toFixed(3))`

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
- Frontend: skeleton = `animate-pulse` divs com `bg-gray-100` — padrão em todas as pages.
- Frontend toast: usar `@/lib/toast` (wrapper com durações padrão) — não `sonner` diretamente.
- ConfirmDialog: `components/ui/confirm-dialog.tsx` — para confirms simples destrutivos.
- Backend Sentry: já implementado em `src/core/sentry.py` — não tocar.
- `@sentry/react` já está no package.json — não reinstalar.
- Sidebar: props `collapsed` + `onToggle`, colapsa em ≤1366px por padrão.

## Iteration 1 - 2026-05-08T19:00:00Z — Issue 14 CONCLUÍDA

### Completed
- Todos os 15 sub-tarefas (A1, A2, B1, C1-C3, D1, E1, F1-F3, G1-G2, H1-H2)
- Commit: c86792c

### Validation Status
- type-check: PASS
- lint: PASS
- build: PASS

---
