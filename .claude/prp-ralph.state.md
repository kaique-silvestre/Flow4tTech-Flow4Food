---
iteration: 2
max_iterations: 20
plan_path: ".claude/PRPs/plans/permissoes-flow4food.md"
started_at: "2026-05-17T00:00:00Z"
---

# Ralph Progress Log

## Codebase Patterns
- Backend usa `Optional[X]` (Python 3.9) mas ruff prefere `X | None` com `from __future__ import annotations`
- Ruff: usar `--unsafe-fixes` para conversão de Optional → `X | None`
- React Query queryKey: `["resource", "subkey", ...params]`
- Zustand store em `frontend/src/stores/`
- tenant_id fixo = 1 (sistema single-tenant)
- JWT novo payload: `user_id, tenant_id, username, profile_id, profile_name, permissions[]`
- `require_permission(screen)` em `dependencies.py` — tokens legados sem `user_id` passam (backward compat)
- Alembic revision ID: manter ≤ 32 chars alfanuméricos; última migration: 0036
- errMsg helper em frontend evita `any` no onError do React Query
- `from __future__ import annotations` + TYPE_CHECKING resolve circular imports entre models

## Iteration 1 — 2026-05-17

### Completed
- Migrations 0034-0036: profiles, profile_permissions, system_users, password_resets; seed Admin/Gerente/Caixa; usuário admin/admin123
- Backend auth service: login por identifier+password, JWT RBAC, change_password
- Frontend: authStore com user/permissions, LoginPage, usePermission, RequirePermission, Sidebar dinâmico, Topbar com logout
- Sprint 2 BE: CRUD users (/api/users) e profiles (/api/profiles) com todas regras de negócio
- Sprint 2 FE: GestaoUsuariosPage, UserModal, ProfileModal, hooks
- Sprint 3 BE: endpoint /api/auth/change-password
- Sprint 3 FE: ChangePasswordModal no Topbar
- Commits: 7dce057, 38732ff, cbc0714

### Validation Status
- Frontend type-check: PASS
- Frontend lint: PASS
- Frontend build: PASS
- Backend ruff: PASS
- Backend imports: PASS
- Migrations: PASS (0034, 0035, 0036 aplicadas)

### Remaining
- #7 BE recuperação de senha (requer SMTP — fora do escopo MVP prático)
- #17 FE fluxo recuperação senha (depende de #7)

### Issues Completas
#1 ✅ #2 ✅ #3 ✅ #4 ✅ #5 ✅ #6 ✅ #8 ✅ #9 ✅ #10 ✅ #11 ✅ #12 ✅ #13 ✅ #14 ✅ #15 ✅ #16 ✅

