# PRP — Issue #3: Cadastros Base (Categorias, Fornecedores, Garçons, Métodos de Pagamento)

**Parent PRD:** `docs/prd_matchpoint_mvp.md`
**Parent Issue:** `docs/issues_matchpoint_mvp.md` → Issue 3
**Documento mestre:** `docs/matchpoint_documentacao.md`
**Type:** AFK
**Status:** Concluída (executada em 2026-05-07, 1 iteração)
**Criado em:** 2026-05-07
**Depende de:** Issue #2 (Auth) — concluída

---

## Objetivo

Quatro CRUDs simples para entidades secundárias usadas pelos módulos seguintes. Telas conforme §8.6.3–8.6.6 do documento mestre. Garçons e Métodos de Pagamento têm soft delete via flag `ativo`; Categorias e Fornecedores têm hard delete. Seed idempotente de dados obrigatórios no banco (migration + serviço Python).

---

## Estrutura de Arquivos Criados/Modificados

```
backend/
  alembic/versions/
    0003_cadastros_base.py              # migration: 4 tabelas + seed SQL

  src/
    models/
      __init__.py                       # (modificado) importa 4 novos models
      categorias.py                     # Categoria(Base): id, nome
      fornecedores.py                   # Fornecedor(Base): id, nome, telefone, email
      garcons.py                        # Garcom(Base): id, nome, ativo
      metodos_pagamento.py              # MetodoPagamento(Base): id, nome, ativo

    schemas/
      categorias.py                     # CategoriaCreateRequest, UpdateRequest, Response
      fornecedores.py                   # FornecedorCreateRequest, UpdateRequest, Response
      garcons.py                        # GarcomCreateRequest, UpdateRequest, Response
      metodos_pagamento.py              # MetodoPagamentoCreateRequest, UpdateRequest, Response

    repositories/
      categorias_repository.py          # list_all, get_by_id, create, update, delete
      fornecedores_repository.py        # list_all, get_by_id, create, update, delete
      garcons_repository.py             # list_all, get_by_id, create, update (sem delete)
      metodos_pagamento_repository.py   # list_all, get_by_id, create, update (sem delete)

    services/
      categorias_service.py             # guard NOT_FOUND, delega ao repo
      fornecedores_service.py           # guard NOT_FOUND, delega ao repo
      garcons_service.py                # guard NOT_FOUND, delega ao repo
      metodos_pagamento_service.py      # guard NOT_FOUND, delega ao repo
      seed_service.py                   # run_seed(db): check-then-insert, idempotente

    api/
      routes/
        categorias.py                   # GET, POST, PUT /{id}, DELETE /{id}
        fornecedores.py                 # GET, POST, PUT /{id}, DELETE /{id}
        garcons.py                      # GET, POST, PUT /{id} (sem DELETE)
        metodos_pagamento.py            # GET, POST, PUT /{id} (sem DELETE)
      main.py                           # (modificado) registra 4 routers

  tests/
    test_cadastros.py                   # 14 testes (CRUD + auth + seed)

frontend/
  src/
    App.tsx                             # (modificado) 4 rotas /cadastros/*
    components/
      layout/
        Sidebar.tsx                     # (modificado) seção Cadastros com 4 links

    features/
      cadastros/
        categorias/
          categoriaSchemas.ts           # Zod: { nome: z.string().min(1) }
          useCategorias.ts              # useQuery + useMutation (create/update/delete)
          CategoriaModal.tsx            # Dialog create/edit
          CategoriasPage.tsx            # lista + botão Nova Categoria

        fornecedores/
          fornecedorSchemas.ts          # Zod: nome, telefone?, email?
          useFornecedores.ts            # useQuery + useMutation (create/update/delete)
          FornecedorModal.tsx           # Dialog create/edit
          FornecedoresPage.tsx          # lista com telefone/email

        garcons/
          garcomSchemas.ts              # garcomSchema (nome+ativo) + garcomCreateSchema (nome)
          useGarcons.ts                 # useQuery + useMutation (create/update)
          GarcomModal.tsx               # Dialog: toggle ativo via switch custom
          GarconsPage.tsx               # lista: inativos com line-through + badge "Inativo"

        metodos_pagamento/
          metodoPagamentoSchemas.ts     # idem garcons
          useMetodosPagamento.ts        # useQuery + useMutation (create/update)
          MetodoPagamentoModal.tsx      # Dialog: toggle ativo via switch custom
          MetodosPagamentoPage.tsx      # lista: inativos com line-through + badge "Inativo"
```

---

## Tarefas

### Bloco A — Migration

- [x] **A1.** Criar `backend/alembic/versions/0003_cadastros_base.py`:
  - `upgrade()`: cria tabelas `categorias`, `fornecedores`, `garcons`, `metodos_pagamento`.
  - Seed SQL via `op.execute()` com `ON CONFLICT (nome) DO NOTHING` (PostgreSQL).
  - `downgrade()`: drop na ordem inversa.

### Bloco B — Models

- [x] **B1.** `models/categorias.py` — `Categoria(Base)`: `id PK`, `nome VARCHAR UNIQUE NOT NULL`.
- [x] **B2.** `models/fornecedores.py` — `Fornecedor(Base)`: `id PK`, `nome`, `telefone?`, `email?`.
- [x] **B3.** `models/garcons.py` — `Garcom(Base)`: `id PK`, `nome`, `ativo BOOL DEFAULT true`.
- [x] **B4.** `models/metodos_pagamento.py` — `MetodoPagamento(Base)`: `id PK`, `nome UNIQUE`, `ativo BOOL DEFAULT true`.
- [x] **B5.** Importar todos em `models/__init__.py` (necessário para Alembic autogenerate).

### Bloco C — Schemas

Padrão: `XCreateRequest`, `XUpdateRequest`, `XResponse(model_config=ConfigDict(from_attributes=True))`.

- [x] **C1.** `schemas/categorias.py`
- [x] **C2.** `schemas/fornecedores.py` — campos `telefone` e `email` com `Optional[str] = None`.
- [x] **C3.** `schemas/garcons.py` — `GarcomUpdateRequest` inclui `ativo: bool`.
- [x] **C4.** `schemas/metodos_pagamento.py` — `MetodoPagamentoUpdateRequest` inclui `ativo: bool`.

### Bloco D — Repositories

Funções puras, sem classes. `db.commit()` + `db.refresh(obj)` após mutação. SQLAlchemy 2.0 (`select()`).

- [x] **D1.** `repositories/categorias_repository.py` — `list_all`, `get_by_id`, `create(nome)`, `update(id, nome)`, `delete(id) -> bool`.
- [x] **D2.** `repositories/fornecedores_repository.py` — `list_all`, `get_by_id`, `create(data)`, `update(id, data)`, `delete(id) -> bool`.
- [x] **D3.** `repositories/garcons_repository.py` — `list_all`, `get_by_id`, `create(data)`, `update(id, data)`. **Sem `delete`** (apenas toggle via update).
- [x] **D4.** `repositories/metodos_pagamento_repository.py` — idem garcons.

### Bloco E — Services

Thin layer. Único papel: guard NOT_FOUND + delegar ao repo.

- [x] **E1–E4.** Services para categorias, fornecedores, garçons, métodos de pagamento.
  - 404: `raise AppError(ErrorCode.NOT_FOUND, "...", http_status=404)` quando `get_by_id` retorna `None`.

- [x] **E5.** `services/seed_service.py` — `run_seed(db: Session)`:
  - Check-then-insert via `select()` (compatível SQLite + PostgreSQL).
  - Seed categorias: `["Geral"]`.
  - Seed métodos: `["PIX", "Crédito", "Débito", "Dinheiro"]`.
  - Idempotente: chamadas múltiplas não criam duplicatas.

### Bloco F — Routes

Todas as rotas: `Depends(get_current_user)` + `Depends(get_db)`.

- [x] **F1.** `api/routes/categorias.py`:
  - `GET /api/categorias` → `list[CategoriaResponse]`
  - `POST /api/categorias` → `CategoriaResponse` (201)
  - `PUT /api/categorias/{id}` → `CategoriaResponse`
  - `DELETE /api/categorias/{id}` → 204

- [x] **F2.** `api/routes/fornecedores.py` — idem categorias.

- [x] **F3.** `api/routes/garcons.py` — sem DELETE:
  - `GET /api/garcons` → todos (incluindo inativos)
  - `POST /api/garcons` → 201
  - `PUT /api/garcons/{id}` → toggle nome/ativo

- [x] **F4.** `api/routes/metodos_pagamento.py` — idem garçons, prefix `/api/metodos-pagamento`.

- [x] **F5.** Registrar 4 routers em `main.py`.

### Bloco G — Tests

- [x] **G1.** `tests/test_cadastros.py` — 14 testes:
  - Fixtures: `crud_client` (override `get_db` + `get_current_user`), `no_auth_client` (override só `get_db`).
  - Seed: `test_seed_idempotente` — `run_seed` 2× → contagem igual.
  - Categorias: CRUD completo + 404 + auth.
  - Fornecedores: CRUD completo + 404 + auth.
  - Garçons: create/list/update + `test_garcom_inativo_aparece_na_lista` + 404 + auth.
  - Métodos: create/list/update + 404 + auth.

### Bloco H — Frontend: Sidebar + Rotas

- [x] **H1.** `Sidebar.tsx` — adicionar seção Cadastros com label separador e 4 `NavLink`:
  - `/cadastros/categorias`, `/cadastros/fornecedores`, `/cadastros/garcons`, `/cadastros/metodos-pagamento`.
  - Items com `to: null` renderizam como `<span>` separador (não `NavLink`).

- [x] **H2.** `App.tsx` — adicionar 4 `<Route>` dentro do bloco autenticado.

### Bloco I — Frontend: Feature Modules

Padrão por módulo: `XPage.tsx` (lista + botão) + `XModal.tsx` (Dialog RHF+Zod) + `xSchemas.ts` + `useX.ts` (useQuery + useMutation).

- [x] **I1.** `features/cadastros/categorias/` — CRUD completo com delete.
- [x] **I2.** `features/cadastros/fornecedores/` — CRUD com campos telefone/email opcionais; string vazia → `null` antes de enviar.
- [x] **I3.** `features/cadastros/garcons/` — sem delete; modal mostra toggle ativo só ao editar; lista: inativos com `line-through text-gray-400` + badge "Inativo".
- [x] **I4.** `features/cadastros/metodos_pagamento/` — idem garçons.

---

## Validações

### Backend
```bash
cd backend
.venv/bin/ruff check .
.venv/bin/mypy src/
.venv/bin/pytest tests/ -v
```

### Frontend
```bash
cd frontend
npm run type-check
npm run lint
npm test
npm run build
```

---

## Critérios de Aceite (do Issue #3)

- [x] Schemas: tabelas `categorias`, `fornecedores`, `garcons`, `metodos_pagamento`.
- [x] Endpoints REST CRUD para cada entidade.
- [x] Soft delete onde fizer sentido (garçom inativo, método desativado) — flag `ativo`.
- [x] Telas frontend: lista + modal de cadastro/edição para cada entidade.
- [x] Garçom: cadastro inclui flag `ativo`. Lista mostra inativos riscados.
- [x] Seed: PIX, Crédito, Débito, Dinheiro pré-cadastrados; categoria "Geral" default. Idempotente.
- [x] Garçom inativado não some de comandas existentes (preserva nome) — contrato testado via `test_garcom_inativo_aparece_na_lista`.
- [x] Testes: CRUD básico, seed idempotente.

---

## Notas Importantes

- **`list[X]` não `List[X]`:** ruff UP006/UP035 força builtin generics. Python 3.9 suporta `list[X]` via PEP 585. Usar `Optional[X]` ainda necessário (não `X | None`).
- **Seed duplo:** migration tem SQL `ON CONFLICT DO NOTHING` (PostgreSQL). `seed_service.py` tem lógica Python check-then-insert (SQLite-compatível, usado nos testes). Migration não roda nos testes (SQLite in-memory via `Base.metadata.create_all`).
- **Garçom sem delete:** Issue #6 (Comandas) referencia garçom pelo id. Deletar causaria FK violation. Toggle `ativo=false` é o soft delete.
- **Métodos sem delete:** idem — Issue #7 (Fechamento) referencia método de pagamento.
- **Fornecedor sem `ativo`:** Issue não especifica soft delete para fornecedor. Hard delete implementado. Issue #5 (Compras) referencia fornecedor; se necessário, adicionar `ativo` no Issue #5.

---

## Tabela de Decisões

| Decisão | Valor | Motivo |
|---|---|---|
| Soft delete garçom/método | `ativo: bool`, sem endpoint DELETE | FK de Issues #6/#7 |
| Hard delete categorias/fornecedores | DELETE endpoint | Sem FKs ainda (Issue #4 cria FK em categorias) |
| Seed via migration + seed_service | Dois mecanismos | Migration = produção; seed_service = testes |
| `list[X]` builtin | ruff UP006 auto-fix | Python 3.9 PEP 585 |
| Toggle ativo via PUT (não PATCH) | Consistência com padrão do repo | Evita partial update logic |

---

## Próximos Passos Pós-Conclusão

Issue #4 (Itens + ficha técnica) consome este foundation:
- `categorias.id` → FK em `itens.categoria_id`.
- `fornecedores.id` → FK em `itens_compra.fornecedor_id` (Issue #5).
- `garcons.id` → FK em `comandas.garcom_id` (Issue #6).
- `metodos_pagamento.id` → FK em `pagamentos.metodo_id` (Issue #7).
- Sidebar ganha links reais de Itens, Estoque, Comandas nas issues seguintes.
- Categorias: ao deletar, verificar se há itens referenciando (guard no service do Issue #4).
