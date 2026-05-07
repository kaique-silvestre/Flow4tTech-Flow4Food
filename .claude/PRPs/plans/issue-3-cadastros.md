# Issue 3 — Cadastros Base

## Tasks

### Backend
- [ ] A. Migration `0003_cadastros_base.py` (4 tables + seed)
- [ ] B. Models: categorias, fornecedores, garcons, metodos_pagamento + update __init__.py
- [ ] C. Schemas: categorias, fornecedores, garcons, metodos_pagamento
- [ ] D. Repositories: categorias, fornecedores, garcons, metodos_pagamento
- [ ] E. Services: categorias, fornecedores, garcons, metodos_pagamento
- [ ] F. Routes: categorias, fornecedores, garcons, metodos_pagamento
- [ ] G. Register routers in main.py
- [ ] H. Tests: test_cadastros.py

### Frontend
- [ ] I. Sidebar nav items for 4 cadastros routes
- [ ] J. App.tsx routes for 4 cadastros pages
- [ ] K. features/cadastros/categorias/ (Page + Modal + Schema + Hook)
- [ ] L. features/cadastros/fornecedores/ (Page + Modal + Schema + Hook)
- [ ] M. features/cadastros/garcons/ (Page + Modal + Schema + Hook, ativo toggle)
- [ ] N. features/cadastros/metodos_pagamento/ (Page + Modal + Schema + Hook, ativo toggle)

## Key Patterns (from Issues 1+2)
- Backend: models → repositories → services → api/routes (pure functions, no classes)
- `AppError(ErrorCode.NOT_FOUND, msg, http_status=404)` for 404s
- All routes: `Depends(get_current_user)` + `Depends(get_db)`
- SQLAlchemy 2.0: `Mapped[Type]`, `mapped_column()`, `select()` syntax
- Python 3.9: `Optional[X]` not `X | None`
- Pydantic: `model_config = ConfigDict(from_attributes=True)` on response schemas
- Frontend: react-hook-form + zodResolver, useMutation invalidates query on success
- Sonner: `toast.success()` on success, `toast.error()` persistent on error
- bcrypt: use `import bcrypt` direct (not passlib) — N/A here but noted

## Validation
```bash
cd backend && .venv/bin/ruff check . && .venv/bin/mypy src/ && .venv/bin/pytest tests/ -v
cd frontend && npm run type-check && npm run lint && npm test && npm run build
```
