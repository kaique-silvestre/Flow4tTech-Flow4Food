---
iteration: 1
max_iterations: 10
plan_path: ".claude/PRPs/plans/issue-5-estoque-compras.md"
started_at: "2026-05-07T15:30:00Z"
completed_at: "2026-05-07T18:20:00Z"
---

# Ralph Progress Log

## Codebase Patterns
- Backend usa `.venv/bin/` para comandos Python (uv ausente no PATH)
- Estrutura Deep Models: models → repositories → services → api/routes (pure functions)
- `AppError(ErrorCode.X, msg, http_status=N)` — de `src.core.errors`
- SQLAlchemy 2.0: `Mapped[Type]`, `mapped_column()`, `select()` syntax
- **Enums SQLAlchemy: usar `sa.Enum(MyEnum, native_enum=False)` — compatibilidade SQLite**
- Python 3.9: usar `Optional[X]` não `X | None`, `list[X]` não `List[X]`
- Pydantic response schemas: `model_config = ConfigDict(from_attributes=True)`
- ruff auto-fix: `.venv/bin/ruff check . --fix --unsafe-fixes`
- Tests: fixture `crud_client` override get_db (SQLite in-memory) + override get_current_user
- Frontend usa npm; imports com `@/` alias
- react-hook-form + zodResolver para forms; `useFieldArray` para listas dinâmicas
- Sonner: `toast.success()` 2-3s, `toast.error()` persistente, `toast.warning()` para avisos
- `useQueryClient().invalidateQueries({ queryKey: [QK] })` após mutações
- Decimal Python: usar `decimal.Decimal` nos models; JSON serializa como string em assertivas de teste

## Iteration 1 - 2026-05-07T18:20:00Z

### Completed
- Migration 0005: compras, itens_compra, movimentos_estoque
- Models: Compra, ItemCompra, MovimentoEstoque (TipoMovimento + MotivoPerda enums)
- Schemas: compras.py + estoque.py (6 schemas)
- Repositories: compras_repository + estoque_repository (list_movimentos com ORDER BY id DESC como tiebreaker)
- Services: compras_service (custo médio ponderado + reset) + estoque_service
- Routes: /api/compras (POST, GET, GET/{id}) + /api/estoque (saldo, baixa-sem-venda, movimentos)
- 14 backend tests — 48/48 passando
- Frontend: compraSchemas, useCompras, ComprasPage, NovaCompraPage (inline fornecedor)
- Frontend: estoqueSchemas, useEstoque, EstoquePage, BaixaSemVendaModal, MovimentosPage
- Sidebar + App.tsx atualizados
- Files changed: 28 files, commit 0e11363

### Validation Status
- ruff: PASS (4 erros auto-fixados)
- mypy (60 files): PASS
- pytest (48 tests): PASS
- Frontend type-check: PASS
- Frontend lint: PASS
- Frontend tests (3): PASS
- Frontend build: PASS

### Learnings
- **SQLite ORDER BY timestamp**: timestamps podem ser iguais em testes rápidos; usar `created_at DESC, id DESC` como tiebreaker
- **Decimal serializado como string**: Pydantic Decimal → JSON string ('200.00'). Assertivas de teste devem usar `float(x) == pytest.approx(y)` não `x == 200.0`
- **custo_medio reset**: condição `estoque_atual <= 0` engloba tanto zero quanto negativo (baixa sem venda antes de comprar)
- **Inline fornecedor**: POST /api/fornecedores (já existente) + refetch após criação; sem necessidade de endpoint especial
- **toast.warning()**: sonner suporta warning para avisos não-destrutivos (saldo negativo)
- **NovaCompraPage**: página completa não modal (form complexo com cabeçalho + N linhas + fornecedor inline)

### Next Steps
- Issue 6: Comandas (abrir, lançar, editar, cancelar item, version conflict 409)

---
