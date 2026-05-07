---
iteration: 1
max_iterations: 10
plan_path: ".claude/PRPs/plans/issue-4-itens.md"
started_at: "2026-05-07T15:00:00Z"
completed_at: "2026-05-07T14:55:00Z"
---

# Ralph Progress Log

## Codebase Patterns
- Backend usa `.venv/bin/` para comandos Python (uv ausente no PATH)
- Estrutura Deep Models: models → repositories → services → api/routes (pure functions)
- `AppError(ErrorCode.X, msg, http_status=N)` — de `src.core.errors`
- ErrorCodes já existentes: NOT_FOUND, FICHA_VAZIA, PRECO_EM_NAO_VENDAVEL, FICHA_ANINHADA_NAO_SUPORTADA
- SQLAlchemy 2.0: `Mapped[Type]`, `mapped_column()`, `select()` syntax
- **Enums SQLAlchemy: usar `sa.Enum(MyEnum, native_enum=False)` — compatibilidade SQLite**
- Python 3.9: usar `Optional[X]` não `X | None`, `list[X]` não `List[X]`
- Pydantic response schemas: `model_config = ConfigDict(from_attributes=True)`
- ruff auto-fix: `.venv/bin/ruff check . --fix --unsafe-fixes`
- Tests: fixture `crud_client` override get_db (SQLite in-memory) + override get_current_user
- Frontend usa npm; imports com `@/` alias
- react-hook-form + zodResolver para forms; `useFieldArray` para listas dinâmicas
- Sonner: `toast.success()` 2-3s, `toast.error()` persistente
- `useQueryClient().invalidateQueries({ queryKey: [QK] })` após mutações
- Decimal Python: usar `decimal.Decimal` nos models; JSON serializa como float

## Iteration 1 - 2026-05-07T14:55:00Z

### Completed
- Migration 0004_itens.py: 3 tabelas (itens, fichas_tecnicas, componentes_ficha)
- Model Item + FichaTecnica + ComponenteFicha com TipoItem + UnidadeBase enums
- Schemas: ComponenteRequest, ComponenteResponse (com insumo_nome), ItemCreateRequest, ItemUpdateRequest, ItemResponse
- Repository: list_with_filters, get_by_id, create, update, soft_delete, hard_delete, upsert_ficha_tecnica, is_referenced_in_ficha, calcular_custo_composto, list_simples_ativos
- Service: _validate_domain, _build_response (custo_composto + cmv%), create/update/delete_item
- Routes: GET /api/itens, GET /api/itens/simples, GET /api/itens/{id}, POST, PUT, DELETE
- 12 backend tests — 34/34 passando
- Frontend: itemSchemas.ts, useItens.ts, ItensPage.tsx, ItemModal.tsx (useFieldArray + CMV real-time)
- Sidebar + App.tsx atualizados
- Files changed: 19 files, commit 1b018dc

### Validation Status
- ruff: PASS
- mypy (50 files): PASS
- pytest (34 tests): PASS
- Frontend type-check: PASS
- Frontend lint: PASS
- Frontend tests (3): PASS
- Frontend build: PASS

### Learnings
- `upsert_ficha_tecnica`: strategy delete-all-then-insert funciona com SQLite (sem ON CONFLICT complexo)
- custo_composto calculado no service (backend) como Σ(qtd × custo_medio) — null se qualquer insumo sem custo
- custo_composto também calculado no frontend para display real-time no modal (useWatch + useMemo)
- mypy: update() retorna Optional[Item] — precisa de null check explícito após chamada
- insumo_nome in ComponenteResponse requer JOIN; feito via `get_componentes()` que carrega insumo

### Next Steps
- Issue 5: Compras + Entradas de Estoque (atualiza custo_medio dos itens)

---
