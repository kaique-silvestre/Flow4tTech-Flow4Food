# PRP — Issue #4: Itens (simples, composto, ficha técnica, soft delete)

**Parent PRD:** `docs/prd_matchpoint_mvp.md`
**Parent Issue:** `docs/issues_matchpoint_mvp.md` → Issue 4
**Documento mestre:** `docs/matchpoint_documentacao.md` §6.2, §8.6.1, §8.6.2
**Type:** HITL (modelo central, validações de domínio)
**Status:** Pronto para execução
**Criado em:** 2026-05-07
**Depende de:** Issue #3 (Cadastros Base) — concluída

---

## Objetivo

Cadastro completo de itens com suporte a tipo simples e composto. Item composto tem ficha técnica com insumos (itens simples) e quantidades; o custo do composto é calculado automaticamente (Σ quantidade × custo_medio do insumo). Três validações de domínio com ErrorCodes já existentes. Soft delete: item referenciado em ficha não pode ser hard-deletado (vira `ativo=false`). Frontend com lista filtrada e tela de cadastro/edição com seção de ficha técnica condicional e CMV calculado em tempo real.

---

## Estrutura de Arquivos a Criar/Modificar

```
backend/
  alembic/versions/
    0004_itens.py                         # migration: itens, fichas_tecnicas, componentes_ficha

  src/
    models/
      __init__.py                         # (modificar) importar 3 novos models
      itens.py                            # Item, TipoItem(enum), UnidadeBase(enum)
      fichas_tecnicas.py                  # FichaTecnica (1:1 com Item composto)
      componentes_ficha.py                # ComponenteFicha (N por FichaTecnica)

    schemas/
      itens.py                            # ItemCreateRequest, ItemUpdateRequest, ItemResponse
                                          # FichaTecnicaRequest, ComponenteRequest
                                          # ItemListResponse (com custo_composto calculado)

    repositories/
      itens_repository.py                 # list_with_filters, get_by_id, create, update,
                                          # soft_delete, upsert_ficha_tecnica

    services/
      itens_service.py                    # validações domínio + soft delete + cálculo custo

    api/
      routes/
        itens.py                          # GET (filtros), POST, PUT /{id},
                                          # DELETE /{id}, PUT /{id}/ficha-tecnica

    main.py                               # (modificar) registrar router itens

  tests/
    test_itens.py                         # validações + custo + soft delete

frontend/
  src/
    App.tsx                               # (modificar) rota /cadastros/itens
    components/
      layout/
        Sidebar.tsx                       # (modificar) link "Itens" na seção Cadastros

    features/
      cadastros/
        itens/
          itemSchemas.ts                  # Zod: ItemFormValues com ficha_tecnica array
          useItens.ts                     # useQuery(list+filters) + mutations
          ItensPage.tsx                   # lista com filtros (radio tipo, dropdown cat, vendavel)
          ItemModal.tsx                   # create/edit; seção ficha técnica condicional;
                                          # custo calculado + CMV em tempo real
```

---

## Modelo de Dados

### Tabelas

```sql
itens (
  id            INTEGER PRIMARY KEY,
  nome          VARCHAR(150) NOT NULL,
  categoria_id  INTEGER REFERENCES categorias(id) NULLABLE,
  tipo          VARCHAR NOT NULL CHECK(tipo IN ('simples','composto')),
  vendavel      BOOLEAN NOT NULL DEFAULT FALSE,
  unidade_base  VARCHAR NOT NULL CHECK(unidade_base IN ('un','g')),
  quantidade_caixa INTEGER NULLABLE,
  custo_medio   NUMERIC(10,4) NULLABLE,
  preco_venda   NUMERIC(10,2) NULLABLE,
  estoque_atual NUMERIC(12,4) NOT NULL DEFAULT 0,
  ativo         BOOLEAN NOT NULL DEFAULT TRUE
)

fichas_tecnicas (
  id                INTEGER PRIMARY KEY,
  item_composto_id  INTEGER UNIQUE NOT NULL REFERENCES itens(id)
)

componentes_ficha (
  id               INTEGER PRIMARY KEY,
  ficha_tecnica_id INTEGER NOT NULL REFERENCES fichas_tecnicas(id),
  insumo_id        INTEGER NOT NULL REFERENCES itens(id),
  quantidade       NUMERIC(10,4) NOT NULL
)
```

### Enums Python

```python
import enum

class TipoItem(str, enum.Enum):
    SIMPLES = "simples"
    COMPOSTO = "composto"

class UnidadeBase(str, enum.Enum):
    UNIDADE = "un"
    GRAMA = "g"
```

---

## Tarefas

### Bloco A — Migration

- [ ] **A1.** `alembic/versions/0004_itens.py`:
  - `upgrade()`: criar tabelas `itens`, `fichas_tecnicas`, `componentes_ficha` na ordem (respeitar FKs).
  - `downgrade()`: drop na ordem inversa.
  - Sem seed.

### Bloco B — Models

- [ ] **B1.** `models/itens.py`:
  ```python
  import enum
  class TipoItem(str, enum.Enum): SIMPLES="simples"; COMPOSTO="composto"
  class UnidadeBase(str, enum.Enum): UNIDADE="un"; GRAMA="g"
  class Item(Base):
      __tablename__ = "itens"
      id, nome, categoria_id(FK nullable), tipo(Enum), vendavel(bool default False),
      unidade_base(Enum), quantidade_caixa(Optional[int]),
      custo_medio(Optional[Decimal]), preco_venda(Optional[Decimal]),
      estoque_atual(Decimal default 0), ativo(bool default True)
  ```
  Usar `sa.Numeric(10, 4)` para custo/estoque, `sa.Numeric(10, 2)` para preco_venda.

- [ ] **B2.** `models/fichas_tecnicas.py`:
  ```python
  class FichaTecnica(Base):
      __tablename__ = "fichas_tecnicas"
      id, item_composto_id(FK UNIQUE NOT NULL)
  ```

- [ ] **B3.** `models/componentes_ficha.py`:
  ```python
  class ComponenteFicha(Base):
      __tablename__ = "componentes_ficha"
      id, ficha_tecnica_id(FK NOT NULL), insumo_id(FK NOT NULL),
      quantidade(Numeric(10,4) NOT NULL)
  ```

- [ ] **B4.** Importar 3 models em `models/__init__.py`.

### Bloco C — Schemas

- [ ] **C1.** `schemas/itens.py`:
  - `ComponenteRequest(insumo_id: int, quantidade: Decimal)` — linha de ficha.
  - `FichaTecnicaRequest(componentes: list[ComponenteRequest])` — min 1 componente.
  - `ItemCreateRequest(nome, categoria_id?, tipo, vendavel, unidade_base, quantidade_caixa?, preco_venda?, ficha_tecnica?)`.
  - `ItemUpdateRequest` — idem ItemCreateRequest.
  - `ComponenteResponse(insumo_id, insumo_nome, quantidade, unidade_base)` — inclui nome do insumo para display.
  - `ItemResponse(model_config from_attributes)` — todos campos + `custo_composto: Optional[Decimal]` calculado, `cmv_percentual: Optional[Decimal]`.
  - `ItemListFilters(categoria_id?, tipo?, vendavel?, busca?)` — Query params.

### Bloco D — Repository

- [ ] **D1.** `repositories/itens_repository.py`:
  - `list_with_filters(db, categoria_id?, tipo?, vendavel?, busca?) -> list[Item]` — só `ativo=True`.
  - `get_by_id(db, item_id) -> Optional[Item]`.
  - `create(db, data: ItemCreateRequest) -> Item`.
  - `update(db, item_id, data: ItemUpdateRequest) -> Optional[Item]`.
  - `soft_delete(db, item_id) -> bool` — seta `ativo=False`.
  - `hard_delete(db, item_id) -> bool` — apenas se sem referências.
  - `is_referenced_in_ficha(db, item_id) -> bool` — checa `ComponenteFicha.insumo_id`.
  - `upsert_ficha_tecnica(db, item_id, componentes: list[ComponenteRequest]) -> FichaTecnica` — delete+insert dos componentes (abordagem simples, sem diff).
  - `get_ficha(db, item_id) -> Optional[FichaTecnica]`.
  - `calcular_custo_composto(db, item_id) -> Optional[Decimal]` — Σ (comp.quantidade × insumo.custo_medio). Retorna None se qualquer insumo sem custo.

### Bloco E — Service (validações de domínio)

- [ ] **E1.** `services/itens_service.py`:

  **Validação ao criar/editar:**
  - `PRECO_EM_NAO_VENDAVEL`: se `vendavel=False` e `preco_venda` não-nulo → raise.
  - `FICHA_ANINHADA_NAO_SUPORTADA`: se tipo=composto e algum insumo da ficha tem `tipo=composto` → raise.
  - `FICHA_VAZIA`: se tipo=composto e ficha_tecnica ausente ou sem componentes → raise (só ao salvar, não ao criar rascunho sem ficha ainda).

  **Soft delete:**
  - Se `is_referenced_in_ficha(item_id)` → `soft_delete` (ativo=False).
  - Caso contrário → `hard_delete`.

  **Cálculo custo:**
  - `get_item_response(db, item) -> ItemResponse`: calcula `custo_composto` e `cmv_percentual` para compostos.

### Bloco F — Routes

Todas as rotas: `Depends(get_current_user)`.

- [ ] **F1.** `api/routes/itens.py`:
  - `GET /api/itens` — query params: `categoria_id?`, `tipo?`, `vendavel?`, `busca?`.
  - `POST /api/itens` — 201.
  - `GET /api/itens/{id}` — retorna item com ficha técnica expandida.
  - `PUT /api/itens/{id}` — atualiza dados + ficha (se composto).
  - `DELETE /api/itens/{id}` — soft ou hard delete conforme referências.
  - `PUT /api/itens/{id}/ficha-tecnica` — substitui ficha completa.

- [ ] **F2.** Registrar em `main.py`: `prefix="/api/itens"`.

### Bloco G — Tests

- [ ] **G1.** `tests/test_itens.py`:
  - Setup: mesmo padrão (`crud_client` com override `get_db` + `get_current_user`).
  - `test_criar_item_simples` — campos básicos, sem ficha.
  - `test_criar_item_composto_com_ficha` — 2 insumos, verificar custo calculado.
  - `test_ficha_vazia_bloqueia_salvar` — composto sem componentes → 400 FICHA_VAZIA.
  - `test_preco_em_nao_vendavel` — vendavel=False + preco_venda → 400 PRECO_EM_NAO_VENDAVEL.
  - `test_ficha_aninhada_bloqueada` — insumo composto em ficha → 400 FICHA_ANINHADA_NAO_SUPORTADA.
  - `test_custo_composto_calculado` — custo = Σ (qtd × custo_medio insumo).
  - `test_soft_delete_preserva_ficha` — item referenciado em ficha → ativo=False, não deletado.
  - `test_hard_delete_sem_referencia` — item sem referências → deletado.
  - `test_filtros_lista` — filtrar por tipo, categoria, vendavel.
  - `test_inativo_some_da_lista` — ativo=False não aparece no GET /api/itens.

### Bloco H — Frontend: Sidebar + Rota

- [ ] **H1.** `Sidebar.tsx` — adicionar `{ label: "Itens", to: "/cadastros/itens" }` após "Categorias".
- [ ] **H2.** `App.tsx` — `<Route path="/cadastros/itens" element={<ItensPage />} />`.

### Bloco I — Frontend: Feature Module

- [ ] **I1.** `itemSchemas.ts`:
  ```ts
  componenteSchema = z.object({ insumo_id: z.number(), quantidade: z.number().positive() })
  itemSchema = z.object({
    nome, categoria_id (optional), tipo, vendavel, unidade_base,
    quantidade_caixa (optional), preco_venda (optional),
    ficha_tecnica: z.array(componenteSchema).optional()
  }).refine(/* vendavel=false → preco_venda null */)
  ```

- [ ] **I2.** `useItens.ts`:
  - `useItens(filters)` — `useQuery` com queryKey `["itens", filters]`.
  - `useCreateItem`, `useUpdateItem`, `useDeleteItem` — mutations com invalidação.
  - `useUpdateFichaTecnica(id)` — mutation PUT /ficha-tecnica.
  - `useCategorias()` — re-export ou import de features/cadastros/categorias.

- [ ] **I3.** `ItensPage.tsx`:
  - Filtros: radio "Todos/Simples/Composto", select Categoria (lista dinâmica), select Vendável "Todos/Sim/Não".
  - Tabela: Nome | Categoria | Tipo | Vendável | Preço (ou "—").
  - Botão "Novo Item" → abre ItemModal.
  - Linha clicável → abre ItemModal em modo edição.
  - Skeleton 3 linhas durante loading; empty state "Nenhum item cadastrado."

- [ ] **I4.** `ItemModal.tsx`:
  - Campos sempre visíveis: Nome, Categoria (select), Tipo (radio), Vendável (checkbox), Unidade (radio).
  - Condicional: "Vem em caixa?" + `quantidade_caixa` (só se unidade=un).
  - Condicional: `preco_venda` (só se vendavel=true).
  - Condicional: seção FICHA TÉCNICA (só se tipo=composto):
    - Tabela de componentes: select insumo (itens simples), input quantidade, unidade (read-only do insumo), botão ✕.
    - Botão "+ Adicionar insumo".
    - Display "Custo calculado: R$ X,XX" — calculado no FE em tempo real.
    - Display "CMV: X,X%" — só se preco_venda preenchido.
  - Usa `useForm` + `useFieldArray` (react-hook-form) para os componentes da ficha.
  - Modal scroll se conteúdo > viewport.

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

## Critérios de Aceite (do Issue #4)

- [ ] Schemas: `itens` (com `ativo`), `ficha_tecnica`, `componente_ficha`.
- [ ] `Item` tem `tipo`, `vendavel`, `unidade_base`, `quantidade_caixa`, `custo_medio`, `preco_venda`, `estoque_atual`.
- [ ] Endpoints: CRUD item, GET com filtros (categoria, tipo, vendável), PUT ficha técnica.
- [ ] Validação: composto exige ≥1 insumo (código `FICHA_VAZIA`).
- [ ] Validação: item não-vendável sem `preco_venda` (código `PRECO_EM_NAO_VENDAVEL`).
- [ ] Validação: ficha não pode incluir outro composto (código `FICHA_ANINHADA_NAO_SUPORTADA`).
- [ ] Soft delete: item referenciado → `ativo=false`; inativo some das buscas.
- [ ] Cálculo custo composto: Σ (quantidade × custo_medio do insumo).
- [ ] FE: lista com filtros; cadastro/edição com ficha técnica condicional + CMV em tempo real.
- [ ] Testes: validações, cálculo de custo, soft delete.

---

## Notas Importantes

- **ErrorCodes já existem** em `src/core/errors.py`: `FICHA_VAZIA`, `PRECO_EM_NAO_VENDAVEL`, `FICHA_ANINHADA_NAO_SUPORTADA`, `NOT_FOUND`.
- **Enums SQLAlchemy:** usar `sa.Enum(TipoItem, native_enum=False)` para compatibilidade com SQLite nos testes.
- **Decimal nos schemas Pydantic:** usar `Decimal` do módulo `decimal`; no response serializado como float via JSON.
- **custo_medio inicial:** `None` (não há compra ainda). Custo do composto retorna `None` se qualquer insumo sem custo.
- **Ficha técnica — upsert:** delete todos componentes existentes + insert novos (abordagem simples). Evita lógica de diff.
- **useFieldArray (RHF):** padrão para lista dinâmica de componentes na UI. Importar de `react-hook-form`.
- **CMV no FE:** calculado em tempo real sem chamada API. Fórmula: Σ(qtd × custo_medio_insumo) / preco_venda × 100.
- **Insumos no select da ficha:** apenas itens com `tipo=simples` e `ativo=True` aparecem.
- **quantidade_caixa:** só relevante se `unidade_base=un`. Armazenado no banco; sem lógica de negócio adicional no MVP.

---

## Tabela de Decisões

| Decisão | Valor | Motivo |
|---|---|---|
| Enum storage | `native_enum=False` (VARCHAR) | Compatibilidade SQLite nos testes |
| Ficha upsert | delete + insert (sem diff) | Simplicidade; ficha não é grande |
| custo_composto | calculado no service, retornado no response | Não persistido — deriva de custo_medio dos insumos |
| Soft vs hard delete | depende de `is_referenced_in_ficha` | Preservar histórico de comandas futuras |
| CMV no FE | calculado no cliente | Sem round-trip; insumos já carregados no form |
| Filtros lista | query params opcionais | Sem paginação no MVP (número de itens pequeno) |

---

## Próximos Passos Pós-Conclusão

Issue #5 (Estoque & Compras) consome diretamente:
- `itens.id` → FK em `itens_compra.item_id` e `movimento_estoque.item_id`.
- `itens.custo_medio` → atualizado pela lógica de custo médio ponderado nas compras.
- `itens.estoque_atual` → atualizado pelos movimentos de entrada/saída.
- `itens.unidade_base` → usado no display de quantidades de estoque.
- Guard de delete em categorias (Issue #3) deve verificar `itens.categoria_id` antes de remover.
