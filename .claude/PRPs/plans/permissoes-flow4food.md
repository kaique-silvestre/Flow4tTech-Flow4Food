# Plano — Gerenciamento de Permissões por Perfil (MVP)

> Baseado em: docs/issues/issues-permissoes-flow4food.md

## Contexto da codebase

- Sistema single-tenant (tenant_id fixo = 1)
- Auth atual: senha única → JWT com `{"sub": "estabelecimento"}`
- Nova auth: usuário/email + senha → JWT com `user_id, tenant_id, username, profile_id, profile_name, permissions[]`
- Backend: FastAPI + SQLAlchemy + Alembic + bcrypt + jose
- Frontend: React + Zustand + React Query + React Router

## Mapeamento de telas → screen identifiers

| Screen ID         | Rotas frontend              |
|-------------------|-----------------------------|
| dashboard         | /                           |
| comandas          | /comandas/*, /cardapio      |
| compras           | /compras/*                  |
| estoque           | /estoque/*                  |
| cadastros         | /cadastros/*                |
| relatorios        | /relatorios/*               |
| configuracoes     | /configuracoes              |
| gestao_usuarios   | /configuracoes/usuarios     |

## Sprint 1 — Fundação

- [ ] #1 BE Migrations (profiles, permissions, users, password_resets)
- [ ] #2 BE Seed perfis padrão (Admin 8/8, Gerente 6/8, Caixa 3/8)
- [ ] #3 BE Auth login/logout (substituir senha única por user+pass)
- [ ] #4 BE Middleware autorização por tela
- [ ] #9 FE Tela de login (atualizar para identifier + senha)
- [ ] #10 FE AuthContext + guards de rota com permissões
- [ ] #11 FE Menu lateral dinâmico por permissão

## Sprint 2 — Gestão de usuários e perfis

- [ ] #5 BE CRUD usuários
- [ ] #6 BE CRUD perfis e permissões
- [ ] #12 FE Tela gestão usuários (/configuracoes/usuarios)
- [ ] #13 FE Modal cadastro/edição usuário
- [ ] #14 FE Tela gestão perfis (tab)
- [ ] #15 FE Modal cadastro/edição perfil

## Sprint 3 — Senhas

- [ ] #7 BE Recuperação de senha
- [ ] #8 BE Alterar própria senha
- [ ] #16 FE Modal alterar própria senha
- [ ] #17 FE Fluxo recuperação de senha

## Validações a cada iteração

```powershell
# Frontend
cd frontend && npm run type-check && npm run lint && npm run build

# Backend
cd backend && .venv\Scripts\Activate.ps1
uv run ruff check
alembic upgrade head
```
