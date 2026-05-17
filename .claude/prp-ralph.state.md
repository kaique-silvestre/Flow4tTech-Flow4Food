---
iteration: 1
max_iterations: 20
plan_path: ".claude/PRPs/plans/permissoes-flow4food.md"
started_at: "2026-05-17T00:00:00Z"
---

# Ralph Progress Log

## Codebase Patterns
- Backend usa `Optional[X]` (Python 3.9), não `X | None`
- Ruff UP035: usar `dict[x]`, `list[x]` nativos, não `Dict`/`List` do typing
- React Query queryKey: `["resource", "subkey", ...params]`
- Zustand store em `frontend/src/stores/`
- tenant_id fixo = 1 (sistema single-tenant)
- JWT atual: `{"sub": "estabelecimento"}` → será substituído por payload RBAC completo
- `get_current_user` em `dependencies.py` precisa ser atualizado para retornar payload enriquecido
- Alembic revision ID: manter ≤ 32 chars alfanuméricos
- Migration mais recente: 0033_fix_tipos_e_padrao_metodos_pagamento.py

