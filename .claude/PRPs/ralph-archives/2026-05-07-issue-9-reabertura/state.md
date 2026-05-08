---
iteration: 1
max_iterations: 10
plan_path: ".claude/PRPs/plans/issue-9-reabertura.md"
started_at: "2026-05-07T00:00:00Z"
---

# Ralph Progress Log

## Codebase Patterns
- Models use `Mapped`/`mapped_column` from `sqlalchemy.orm`, Base from `src.core.database`
- Enums use `str, enum.Enum` with `native_enum=False` in column defs
- Services raise `AppError(ErrorCode.X, "msg", http_status=N)`
- Tests use real SQLite in-memory + `Base.metadata.create_all(_engine)`
- Schemas use Pydantic v2 `BaseModel`, `ConfigDict(from_attributes=True)` on responses
- Routes: `Depends(get_current_user)` + `Depends(get_db)` on all endpoints
- Python 3.9: `Optional[X]` não `X | None`
- `db.flush()` após cada insert intermediário; `db.commit()` único no final (atomicidade)
- SQLite NUMERIC Decimal precision: use float() in test assertions, not string equality
- Validation commands (from backend dir): `ruff check .` + `mypy src/` + `pytest tests/ -v`
- Frontend validation: `npm run type-check && npm run lint && npm run build` (from frontend dir)
- Tools in PATH: ruff, mypy, pytest (no .venv needed)
- `ruff check . --fix` auto-fixes import ordering
- GET /fechadas must be declared BEFORE GET /{comanda_id} in the same router (FastAPI path param conflict)
- `add_evento(db, comanda_id, TipoEvento.X, {}, garcom_id)` — fourth arg is payload dict
- `get_itens_para_fechar(db, comanda_id)` returns non-cancelled items — reuse for reopening
- `StatusComanda`, `TipoEvento`, `TipoMovimento` are string enums stored in VARCHAR — no migration needed for new values
- `registrar_movimento(db, item.id, TipoMovimento.X, quantidade, custo_unitario, saldo_apos)` — signature

