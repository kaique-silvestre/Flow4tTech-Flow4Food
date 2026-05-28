# PRP — Issue #1: RLS Migrations Foundation (Multi-Tenant)

**Parent Issues doc:** `docs/issues/issues_v1_lancamento_comercial.md` → Issue 1
**Type:** HITL
**Status:** Em execução
**Criado em:** 2026-05-28

---

## Objetivo

Criar tabela `tenants`, adicionar `tenant_id NOT NULL` a todas as tabelas operacionais, habilitar Row-Level Security com policy `tenant_isolation` em cada tabela, e criar índices compostos com `tenant_id` como primeira coluna.

---

## Tabelas Alvo

Recebem `tenant_id` + RLS:
`comandas`, `itens_comanda`, `insumos`, `produtos`, `movimentos_estoque`, `compras`, `pagamentos`, `comissoes_garcom`, `eventos_comanda`, `categorias`, `fornecedores`, `profiles`, `profile_permissions`, `system_users`

Nota: `profiles` e `system_users` já têm `tenant_id` (server_default="1") — precisam apenas de FK para `tenants` + RLS.

---

## Tarefas

### Bloco A — Migrations

- [x] **A1.** `0042_create_tenants.py`: CREATE TABLE tenants (id, nome_fantasia, cnpj, status, admin_user_id, created_at). Seed tenant id=1.
- [x] **A2.** `0043_add_tenant_id_rls.py`:
  - Adicionar `tenant_id BIGINT NOT NULL DEFAULT 1` nas tabelas sem tenant_id
  - Adicionar FK tenant_id → tenants.id em `profiles` e `system_users`
  - Adicionar `tenant_id` + FK em `profile_permissions`, `comandas`, `itens_comanda`, `insumos`, `produtos`, `movimentos_estoque`, `compras`, `pagamentos`, `comissoes_garcom`, `eventos_comanda`, `categorias`, `fornecedores`
  - PostgreSQL-only: ENABLE ROW LEVEL SECURITY + CREATE POLICY tenant_isolation em cada tabela
  - Índices compostos (tenant_id, id) para tabelas de alta leitura

### Bloco B — Models SQLAlchemy

- [x] **B1.** Adicionar `tenant_id: Mapped[int]` nos models: `Comanda`, `ItemComanda`, `Insumo`, `Produto`, `MovimentoEstoque`, `Compra`, `Pagamento`, `ComissaoGarcom`, `EventoComanda`, `Categoria`, `Fornecedor`
- [x] **B2.** Adicionar `tenant_id: Mapped[int]` em `ProfilePermission`
- [x] **B3.** Criar `src/models/tenants.py` com model `Tenant`

### Bloco C — Testes

- [x] **C1.** `tests/test_rls.py`: testes de isolamento RLS (skip se não PostgreSQL)
  - Teste: query com app.tenant_id=1 não retorna registros de tenant_id=2
  - Teste: query sem SET app.tenant_id retorna 0 linhas

---

## Validações

```bash
cd backend
ruff check src/ tests/
mypy src/
pytest -q
alembic upgrade head  # em banco limpo
```

---

## Acceptance Criteria (do Issue)

- [x] Migration `tenants` criada: id, nome_fantasia, cnpj, status, admin_user_id, created_at
- [x] tenant_id NOT NULL adicionado a todas as tabelas operacionais listadas
- [x] ENABLE ROW LEVEL SECURITY + CREATE POLICY tenant_isolation em cada tabela
- [x] Índices compostos (tenant_id, id) criados para tabelas de alta leitura
- [x] system_users.email permite NULL; unique se preenchido (já satisfeito)
- [x] Teste de isolamento RLS: query com app.tenant_id=1 não retorna registros de tenant 2
- [x] Teste de bloqueio: query sem SET app.tenant_id retorna 0 linhas
- [x] Migrations rodam do zero sem erro (alembic upgrade head em banco limpo)

---

## Notas

- RLS é PostgreSQL-only. Migration usa `op.get_bind().dialect.name == 'postgresql'` guard.
- Tests RLS usam `pytest.mark.skipif` se DATABASE_URL não for PostgreSQL.
- `current_setting('app.tenant_id', true)` com segundo arg True = missing_ok (retorna '' se não setado, não erro).
- NULLIF('', '') retorna NULL → tenant_id = NULL é falso → 0 linhas (comportamento de bloqueio correto).
- `profiles` e `system_users`: server_default="1" permanece para compatibilidade; FK adicionada via migration separada.
