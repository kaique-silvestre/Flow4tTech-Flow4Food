---
iteration: 9
max_iterations: 10
plan_path: "docs/issues/issues_matchpoint_v0.4.md"
started_at: "2026-05-13T00:00:00Z"
---

# Ralph Progress Log

## Codebase Patterns
- Backend uses `Optional[X]` (Python 3.9), not `X | None`
- Ruff UP035: use native `dict[x]`, `list[x]`, not `Dict`/`List` from typing
- React Query queryKey pattern: `["resource", "subkey", ...params]`
- Dialog component at `@/components/ui/dialog`
- RHF radio with register: order in array controls render order
- defaultValues in useForm controls initial selection
- MoneyInput em `@/components/ui/money-input` — props: value, onValueChange(rawString), id, className, placeholder
- Para integrar MoneyInput+RHF: usar Controller; onValueChange recebe string numérica sem máscara (ex: "1050.00")
- custo_unitario em NovaCompraPage é UI-only (não RHF) → bind direto com onValueChange
- custo_total é RHF number → Controller + field.onChange(parseFloat(raw))

## Iteration 1 - 2026-05-13T00:00:00Z

### Completed
- `NovaComandaModal.tsx` linha 37: `tipo_identificacao: "mesa"` → `"nome"` (default)
- `NovaComandaModal.tsx` linha 90: array `["mesa","nome"]` → `["nome","mesa"]` (ordem)
- Commit: 62ffd5f

### Validation Status
- Type-check: PASS
- Lint: PASS
- Build: PASS

### Learnings
- `use-debounce` já estava em package.json (commit bae9b34 do v0.3)
- Ordem do array no `.map()` controla ordem visual dos radios

### Issue 1: COMPLETA ✅

---

## Iteration 2 - 2026-05-13T01:00:00Z

### Completed
- `backend/src/api/routes/produtos.py`: `ativo: Optional[bool] = Query(None)` + repassa para service
- `backend/src/services/produtos_service.py`: `list_produtos` aceita e repassa `ativo`
- `frontend/src/features/cadastros/produtos/useProdutos.ts`: `options?: { ativo?: boolean }` no queryKey + params
- `frontend/src/features/comandas/ComandaAbertaPage.tsx`: passa `{ ativo: true }` para `useProdutos`
- `backend/tests/test_produtos.py`: 2 testes corrigidos para usar `?ativo=true`
- Commit: ce53555

### Validation Status
- Type-check: PASS
- Lint: PASS
- Backend ruff: PASS
- Backend testes produto: 9/9 PASS
- Build: PASS
- 43 outras falhas backend pré-existentes (não relacionadas)

### Learnings
- `GET /api/produtos` sem param retorna todos — CardapioPage depende disso
- 2 testes pré-existentes assumiam comportamento incorreto — corrigidos

### Issue 2: COMPLETA ✅

---

## Iteration 3 - 2026-05-13T02:00:00Z

### Completed
- `CardapioPage.tsx`: importou `Categoria` type de useCategorias
- `CardapioPage.tsx`: adicionou `buildCategoryPaths(tree, prefix)` recursivo → `Record<number, string>`
- `CardapioPage.tsx`: substituiu `catMap` por `catPathMap`
- Célula de categoria agora exibe "Pai > Filho" ou só "Pai" ou "—"
- Commit: f721e1f

### Validation Status
- Type-check: PASS
- Lint: PASS
- Build: PASS

### Learnings
- `Categoria` já tinha `children: Categoria[]` — nenhuma mudança de backend necessária
- `flattenCategorias` existia mas não preservava path hierárquico — criou-se `buildCategoryPaths` separado

### Issue 4: COMPLETA ✅

---

## Iteration 4 - 2026-05-13T03:00:00Z

### Completed
- `npm install react-number-format` → registrado em package.json
- Criado `frontend/src/components/ui/money-input.tsx` com NumericFormat (R$, vírgula decimal, ponto milhar, 2 casas)
- `ProdutoModal.tsx`: adicionou Controller import + MoneyInput import; substituiu `<Input type="number" ...register("preco_venda")>` por Controller+MoneyInput
- `NovaCompraPage.tsx`: adicionou MoneyInput import; substituiu custo_unitario Input por MoneyInput; refatorou `handleTotalChange` para aceitar `number` em vez de `React.ChangeEvent`; substituiu custo_total register+onChange por Controller+MoneyInput
- Commit: 7253919

### Validation Status
- Type-check: PASS
- Lint: PASS
- Build: PASS

### Learnings
- handleTotalChange antes recebia `React.ChangeEvent` — agora aceita `number` diretamente para compatibilidade com MoneyInput
- `z.coerce.number()` no schema de custo_total: field.onChange precisa receber number, não string

### Issue 5: COMPLETA ✅

---

## Iteration 5 - 2026-05-13T04:00:00Z

### Completed
- `produtoSchemas.ts`: `categoria_id` de `nullable().optional()` → `z.number({ required_error, invalid_type_error })` com `.min(1)`
- `ProdutoModal.tsx`: select com `border-red-500` condicional + erro inline abaixo
- `ProdutoModal.tsx`: `setValueAs` retorna `undefined` (não `null`) para opção vazia — dispara `required_error`
- `ProdutoModal.tsx`: reset novo produto usa `categoria_id: undefined` (não `null`)
- Commit: f678076

### Validation Status
- Type-check: PASS
- Lint: PASS
- Build: PASS

### Learnings
- `invalid_type_error` necessário pois `null` não é `undefined` — sem ele zod diria "Expected number, received null"
- `setValueAs` retornando `undefined` é mais limpo que `null` para campos obrigatórios no Zod

### Issue 6: COMPLETA ✅

---

## Iteration 6 - 2026-05-13T05:00:00Z

### Completed
- `backend/src/models/metodos_pagamento.py`: enum `TipoPagamento` + coluna `tipo` com `server_default="outro"`
- `backend/src/schemas/metodos_pagamento.py`: `tipo: TipoPagamento` em create/update/response
- `backend/src/repositories/metodos_pagamento_repository.py`: `tipo=data.tipo` em create/update
- `backend/alembic/versions/0027_add_tipo_metodo_pagamento.py`: migration additive com `server_default="outro"`
- `frontend/src/features/cadastros/metodos_pagamento/metodoPagamentoSchemas.ts`: enum `TIPOS_PAGAMENTO`, labels, schemas atualizados
- `frontend/src/features/cadastros/metodos_pagamento/useMetodosPagamento.ts`: `tipo: TipoPagamento` na interface
- `frontend/src/features/cadastros/metodos_pagamento/MetodoPagamentoModal.tsx`: select de tipo com 5 opções
- Commit: 6b73d80

### Validation Status
- Type-check: PASS
- Lint: PASS
- Backend ruff: PASS
- Migration: PASS (0027 aplicada)
- Build: PASS

### Learnings
- Migration usa `sa.String()` (não `sa.Enum()`) pois model usa `native_enum=False` — mais portável com SQLite/Postgres
- `MetodoPagamentoCreateFormValues` precisou incluir `tipo` pois modal cria com tipo escolhido pelo usuário

### Issue 7: COMPLETA ✅

---

## Iteration 7 - 2026-05-13T07:00:00Z

### Completed
- `backend/alembic/versions/0028_add_troco_pagamento.py`: migration additive `valor_nota` + `troco` (Numeric 10,2 nullable)
- `backend/src/models/pagamentos.py`: `valor_nota: Mapped[Optional[Decimal]]`, `troco: Mapped[Optional[Decimal]]`
- `backend/src/schemas/fechamento.py`: `PagamentoRequest.valor_nota` opcional; `PagamentoResponse.valor_nota+troco`
- `backend/src/repositories/pagamentos_repository.py`: `create_pagamento` aceita `valor_nota`, `troco`
- `backend/src/services/comandas_service.py`: detecta `metodo.tipo == "dinheiro"` + `valor_nota`, valida, calcula troco; inclui `valor_nota`+`troco` no `PagamentoResponse` ao construir resposta
- `backend/src/schemas/comprovante.py`: `PagamentoComprovanteRow.valor_nota+troco`
- `backend/src/services/comprovante_service.py`: inclui `valor_nota`, `troco` na row
- `frontend/.../fechamentoSchemas.ts`: `valor_nota` opcional no `pagamentoSchema`
- `frontend/.../useFechamento.ts`: `MetodoPagamento.tipo: string`
- `frontend/.../useComprovante.ts`: `PagamentoComprovanteRow.valor_nota+troco`
- `frontend/.../FechamentoPage.tsx`: UI troco inline quando `tipo="dinheiro"` — MoneyInput nota + read-only troco + aviso nota insuficiente
- `frontend/.../ComprovantePage.tsx`: exibe "Valor recebido" e "Troco" quando `troco > 0`
- Commit: 6513eb5

### Validation Status
- Type-check: PASS
- Lint: PASS
- Backend ruff: PASS
- Migration: PASS (0028 aplicada)
- Build: PASS

### Learnings
- `PagamentoResponse` usa `ConfigDict(from_attributes=True)` — campos `valor_nota` e `troco` são preenchidos diretamente do model ORM quando passado, mas neste caso são construídos manualmente; precisam ser passados explicitamente no construtor
- `setValue` para `valor_nota: undefined` ao trocar método garante que campo some ao mudar para não-dinheiro
- `MoneyInput` retorna string numérica via `onValueChange`; usar `parseFloat` para RHF `number` field

### Issue 8: COMPLETA ✅

---

## Iteration 8 - 2026-05-13T08:00:00Z

### Completed
- `backend/alembic/versions/0029_add_estoque_reservado_insumos.py`: migration additive `estoque_reservado` (Numeric 12,4, NOT NULL, server_default=0)
- `backend/src/models/insumos.py`: `estoque_reservado: Mapped[Decimal]` + `server_default="0"`
- `backend/src/schemas/comandas.py`: `estoque_insuficiente: list[str] = []` em `ComandaResponse`
- `backend/src/services/comandas_service.py`: 
  - `_reservar_estoque`: incrementa reserva, retorna nomes onde disponível < 0
  - `_liberar_reserva_estoque`: decrementa reserva com piso em 0
  - `lancar_item`: chama `_reservar_estoque`, anexa ao response
  - `cancelar_item`: chama `_liberar_reserva_estoque` antes do commit
  - `fechar_comanda` (não parcial): chama `_liberar_reserva_estoque` por item além do `_dar_baixa_estoque`
  - `cancelar_comanda`: libera reservas de itens não-cancelados + seta status CANCELADA
- `backend/src/repositories/comandas_repository.py`: `cancelar_comanda_repo` seta status CANCELADA
- `backend/src/api/routes/comandas.py`: `POST /{comanda_id}/cancelar`
- `frontend/.../useComandas.ts`: `estoque_insuficiente` em `ComandaResponse`; `useLancarItem.onSuccess` mostra toasts; `useCancelarComanda` hook
- `frontend/.../ComandaAbertaPage.tsx`: botão "Cancelar Comanda" + ConfirmDialog
- Commit: e16c839

### Validation Status
- Type-check: PASS
- Lint: PASS
- Backend ruff: PASS
- Migration: PASS (0029 aplicada)
- Build: PASS

### Learnings
- Revision ID alembic deve caber em varchar(32) — strings longas causam rollback na versão table
- `get_itens_ativos` retorna TODOS (inclusive cancelados) — usar `get_itens_para_fechar` para liberar reservas ao cancelar comanda inteira
- `_liberar_reserva_estoque` usa piso em zero: `novo if novo > 0 else Decimal("0")`

### Issue 9: COMPLETA ✅

---

## Iteration 9 - 2026-05-13T14:00:00Z

### Completed
- `backend/src/schemas/insumos.py`: `estoque_reservado: Decimal` + `@computed_field estoque_disponivel`
- `backend/src/schemas/estoque.py`: `estoque_reservado: Decimal` + `estoque_disponivel: Decimal` em `SaldoItemResponse`
- `backend/src/services/estoque_service.py`: popula `estoque_reservado` e `estoque_disponivel` em `get_saldo_list`
- `frontend/src/features/estoque/useEstoque.ts`: `estoque_reservado` + `estoque_disponivel` em `SaldoItemResponse`
- `frontend/src/features/estoque/useInsumos.ts`: mesmos campos em `InsumoResponse`
- `frontend/src/features/estoque/EstoquePage.tsx`: colunas "Estoque atual", "Reservado", "Disponível"; Disponível em vermelho quando < 0; colSpan tfoot 4→6
- Commit: 2a8228d

### Validation Status
- Type-check: PASS
- Lint: PASS
- Backend ruff: PASS
- Build: PASS

### Learnings
- Pydantic v2 `@computed_field` + `@property` funciona com `from_attributes=True` — não precisa de campo no model ORM
- `SaldoItemResponse` é construído manualmente no service, então `estoque_disponivel` calculado diretamente no construtor (sem computed_field)

### Issue 10: COMPLETA ✅

---
