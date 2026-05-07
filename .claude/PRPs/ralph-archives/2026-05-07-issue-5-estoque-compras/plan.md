# PRP — Issue #5: Estoque & Compras (saldo, baixa sem venda, histórico, custo médio ponderado)

**Parent PRD:** `docs/prd_matchpoint_mvp.md`
**Parent Issue:** `docs/issues_matchpoint_mvp.md` → Issue 5
**Documento mestre:** `docs/matchpoint_documentacao.md` §8.4, §8.5
**Type:** AFK
**Status:** Pronto para execução
**Criado em:** 2026-05-07
**Depende de:** Issue #4 (Itens) — concluída

---

## Objetivo

Módulos de Compras e Estoque unificados pelo `movimento_estoque`. Uma compra gera movimentos de entrada, atualiza `itens.estoque_atual` e recalcula `itens.custo_medio` por média ponderada (com reset quando estoque anterior ≤ 0). Baixa sem venda gera movimento de saída. Saldo negativo é permitido (toast amarelo no FE). Histórico paginado de todos os movimentos com filtros. FE inclui: Lista de Compras, form Nova Compra (com linha de itens dinâmica e criação inline de fornecedor), Saldo Atual, modal Baixa Sem Venda, e tela Histórico de Movimentações.

---

## Estrutura de Arquivos a Criar/Modificar

```
backend/
  alembic/versions/
    0005_estoque_compras.py             # migration: compras, itens_compra, movimentos_estoque

  src/
    models/
      __init__.py                       # (modificar) importar 3 novos models
      compras.py                        # Compra, ItemCompra
      movimentos_estoque.py             # MovimentoEstoque, TipoMovimento(enum), MotivoPerda(enum)

    schemas/
      compras.py                        # ItemCompraRequest, CompraCreateRequest, CompraResponse, ItemCompraResponse
      estoque.py                        # SaldoResponse, BaixaSemVendaRequest, MovimentoResponse, MovimentoListResponse

    repositories/
      compras_repository.py             # create_compra, list_compras, get_compra_by_id
      estoque_repository.py             # get_saldo, registrar_movimento, list_movimentos, baixa_sem_venda

    services/
      compras_service.py                # criar_compra (custo médio ponderado + movimentos)
      estoque_service.py                # baixa_sem_venda, get_saldo_list, get_historico

    api/
      routes/
        compras.py                      # POST, GET /api/compras; GET /api/compras/{id}
        estoque.py                      # GET saldo, POST baixa-sem-venda, GET movimentos

    main.py                             # (modificar) registrar 2 novos routers

  tests/
    test_compras.py                     # custo médio, reset, filtros período
    test_estoque.py                     # baixa sem venda, histórico, saldo negativo

frontend/
  src/
    App.tsx                             # (modificar) rotas /compras, /compras/nova, /estoque, /estoque/movimentos
    components/
      layout/
        Sidebar.tsx                     # (modificar) links Compras, Estoque, Histórico

    features/
      compras/
        compraSchemas.ts                # Zod: ItemCompraFormValues, CompraFormValues
        useCompras.ts                   # useCompras(filters), useCreateCompra
        ComprasPage.tsx                 # lista compras com filtros período+fornecedor
        NovaCompraPage.tsx              # form compra com linhas dinâmicas + inline fornecedor

      estoque/
        estoqueSchemas.ts               # Zod: BaixaSemVendaFormValues
        useEstoque.ts                   # useSaldoEstoque(filters), useBaixaSemVenda, useMovimentos(filters)
        EstoquePage.tsx                 # saldo atual (só simples) + botão Baixa Sem Venda
        BaixaSemVendaModal.tsx          # modal: item, quantidade, motivo (radio), observação
        MovimentosPage.tsx              # histórico paginado com filtros
```

---

## Modelo de Dados

### Tabelas

```sql
compras (
  id              INTEGER PRIMARY KEY,
  fornecedor_id   INTEGER NULLABLE REFERENCES fornecedores(id),
  data_compra     DATE NOT NULL,
  numero_nota     VARCHAR(50) NULLABLE,
  total           NUMERIC(12,2) NOT NULL DEFAULT 0,
  created_at      TIMESTAMP NOT NULL DEFAULT now()
)

itens_compra (
  id              INTEGER PRIMARY KEY,
  compra_id       INTEGER NOT NULL REFERENCES compras(id),
  item_id         INTEGER NOT NULL REFERENCES itens(id),
  quantidade      NUMERIC(12,4) NOT NULL,
  custo_unitario  NUMERIC(10,4) NOT NULL,
  custo_total     NUMERIC(12,2) NOT NULL
)

movimentos_estoque (
  id              INTEGER PRIMARY KEY,
  item_id         INTEGER NOT NULL REFERENCES itens(id),
  tipo            VARCHAR NOT NULL,  -- entrada | saida_venda | saida_perda
  quantidade      NUMERIC(12,4) NOT NULL,  -- positivo sempre; sinal controlado por tipo
  custo_unitario  NUMERIC(10,4) NULLABLE,
  saldo_apos      NUMERIC(12,4) NOT NULL,
  motivo          VARCHAR NULLABLE,  -- consumo_interno | perda | quebra | cortesia | outro
  observacao      VARCHAR(500) NULLABLE,
  compra_id       INTEGER NULLABLE REFERENCES compras(id),
  created_at      TIMESTAMP NOT NULL DEFAULT now()
)
```

### Enums Python

```python
class TipoMovimento(str, enum.Enum):
    ENTRADA = "entrada"
    SAIDA_VENDA = "saida_venda"
    SAIDA_PERDA = "saida_perda"

class MotivoPerda(str, enum.Enum):
    CONSUMO_INTERNO = "consumo_interno"
    PERDA = "perda"
    QUEBRA = "quebra"
    CORTESIA = "cortesia"
    OUTRO = "outro"
```

### Custo Médio Ponderado

```
Se estoque_anterior <= 0:
    custo_medio_novo = custo_unitario_compra
Senão:
    custo_medio_novo = (estoque_anterior × custo_medio_atual + quantidade × custo_unitario)
                       / (estoque_anterior + quantidade)
```

---

## Tarefas

### Bloco A — Migration

- [ ] **A1.** `alembic/versions/0005_estoque_compras.py`:
  - `down_revision = "0004_itens"`
  - `upgrade()`: criar `compras`, `itens_compra`, `movimentos_estoque` (respeitar FKs).
  - `downgrade()`: drop na ordem inversa.
  - Sem seed.

### Bloco B — Models

- [ ] **B1.** `models/compras.py`:
  ```python
  class Compra(Base):
      __tablename__ = "compras"
      id, fornecedor_id(FK nullable), data_compra(sa.Date),
      numero_nota(Optional[str]), total(Numeric(12,2) default 0), created_at(DateTime server_default)

  class ItemCompra(Base):
      __tablename__ = "itens_compra"
      id, compra_id(FK NOT NULL), item_id(FK NOT NULL),
      quantidade(Numeric(12,4)), custo_unitario(Numeric(10,4)), custo_total(Numeric(12,2))
  ```

- [ ] **B2.** `models/movimentos_estoque.py`:
  ```python
  class TipoMovimento(str, enum.Enum): ENTRADA="entrada"; SAIDA_VENDA="saida_venda"; SAIDA_PERDA="saida_perda"
  class MotivoPerda(str, enum.Enum): CONSUMO_INTERNO="consumo_interno"; PERDA="perda"; QUEBRA="quebra"; CORTESIA="cortesia"; OUTRO="outro"

  class MovimentoEstoque(Base):
      __tablename__ = "movimentos_estoque"
      id, item_id(FK NOT NULL), tipo(Enum native_enum=False),
      quantidade(Numeric(12,4)), custo_unitario(Optional Numeric(10,4)),
      saldo_apos(Numeric(12,4)), motivo(Optional[str]),
      observacao(Optional[str]), compra_id(Optional FK), created_at(DateTime server_default)
  ```

- [ ] **B3.** Importar `Compra`, `ItemCompra`, `MovimentoEstoque` em `models/__init__.py`.

### Bloco C — Schemas

- [ ] **C1.** `schemas/compras.py`:
  - `ItemCompraRequest(item_id: int, quantidade: Decimal > 0, custo_total: Decimal > 0)` — custo_unitario calculado
  - `CompraCreateRequest(fornecedor_id?: int, data_compra: date, numero_nota?: str, itens: list[ItemCompraRequest])` — min 1 item
  - `ItemCompraResponse(item_id, item_nome, quantidade, custo_unitario, custo_total)`
  - `CompraResponse(id, fornecedor_id, fornecedor_nome, data_compra, numero_nota, total, itens: list[ItemCompraResponse], created_at)`

- [ ] **C2.** `schemas/estoque.py`:
  - `SaldoItemResponse(id, nome, categoria_id, categoria_nome, unidade_base, estoque_atual, custo_medio)`
  - `BaixaSemVendaRequest(item_id: int, quantidade: Decimal > 0, motivo: MotivoPerda, observacao?: str)`
  - `MovimentoResponse(id, item_id, item_nome, tipo, quantidade, custo_unitario, saldo_apos, motivo, observacao, compra_id, created_at)`
  - `MovimentoListResponse(itens: list[MovimentoResponse], total: int, pagina: int, por_pagina: int)`

### Bloco D — Repositories

- [ ] **D1.** `repositories/compras_repository.py`:
  - `create_compra(db, data: CompraCreateRequest) -> Compra` — insere cabeçalho; retorna Compra sem itens
  - `add_itens_compra(db, compra_id, itens: list[ItemCompra]) -> None`
  - `list_compras(db, data_inicio?, data_fim?, fornecedor_id?) -> list[Compra]`
  - `get_compra_by_id(db, compra_id) -> Optional[Compra]` — com itens

- [ ] **D2.** `repositories/estoque_repository.py`:
  - `get_item_for_update(db, item_id) -> Optional[Item]` — lock para update
  - `update_estoque_e_custo(db, item_id, novo_estoque, novo_custo_medio) -> None`
  - `registrar_movimento(db, item_id, tipo, quantidade, custo_unitario?, saldo_apos, motivo?, observacao?, compra_id?) -> MovimentoEstoque`
  - `list_saldo(db, categoria_id?, busca?) -> list[Item]` — só simples ativos
  - `list_movimentos(db, item_id?, tipo?, data_inicio?, data_fim?, pagina, por_pagina) -> tuple[list[MovimentoEstoque], int]` — retorna (resultados, total), ordered by created_at DESC

### Bloco E — Services

- [ ] **E1.** `services/compras_service.py` — `criar_compra(db, data: CompraCreateRequest) -> CompraResponse`:
  1. Para cada item em `data.itens`:
     - Buscar Item; 404 se não existe.
     - `custo_unitario = custo_total / quantidade`
     - Aplicar custo médio ponderado (regra de reset se estoque ≤ 0).
     - `update_estoque_e_custo(db, item_id, estoque + quantidade, novo_custo_medio)`
     - `registrar_movimento(db, item_id, ENTRADA, quantidade, custo_unitario, saldo_apos, compra_id=compra.id)`
  2. Calcular total da compra = Σ custo_total dos itens.
  3. Inserir `Compra` com total calculado.
  4. Inserir `ItemCompra` para cada item.
  5. Retornar `CompraResponse`.

- [ ] **E2.** `services/estoque_service.py`:
  - `baixa_sem_venda(db, data: BaixaSemVendaRequest) -> dict` — retorna `{movimento, saldo_negativo: bool}`:
    - Buscar Item; 404 se não existe ou não é simples.
    - `novo_saldo = estoque_atual - quantidade`
    - `update_estoque_e_custo(db, item_id, novo_saldo, custo_medio)` — custo não muda na baixa
    - `registrar_movimento(db, item_id, SAIDA_PERDA, quantidade, None, novo_saldo, motivo, observacao)`
    - `saldo_negativo = novo_saldo < 0`
  - `get_saldo_list(db, categoria_id?, busca?) -> list[SaldoItemResponse]`
  - `get_historico(db, item_id?, tipo?, data_inicio?, data_fim?, pagina, por_pagina) -> MovimentoListResponse`

### Bloco F — Routes

Todas as rotas: `Depends(get_current_user)`.

- [ ] **F1.** `api/routes/compras.py`:
  - `POST /api/compras` → 201 + `CompraResponse`
  - `GET /api/compras` — query params: `data_inicio?` (date), `data_fim?` (date), `fornecedor_id?`
  - `GET /api/compras/{id}` → `CompraResponse` com itens

- [ ] **F2.** `api/routes/estoque.py`:
  - `GET /api/estoque/saldo` — query params: `categoria_id?`, `busca?`
  - `POST /api/estoque/baixa-sem-venda` → 201 + `{movimento, saldo_negativo}`
  - `GET /api/estoque/movimentos` — query params: `item_id?`, `tipo?`, `data_inicio?`, `data_fim?`, `pagina` (default 1), `por_pagina` (default 50)

- [ ] **F3.** Registrar em `main.py`:
  ```python
  app.include_router(compras.router, prefix="/api/compras", tags=["compras"])
  app.include_router(estoque.router, prefix="/api/estoque", tags=["estoque"])
  ```

### Bloco G — Tests

- [ ] **G1.** `tests/test_compras.py`:
  - `test_criar_compra_simples` — 1 item, verifica custo_medio e estoque_atual atualizados.
  - `test_custo_medio_ponderado` — 2 compras sequenciais: custo1=2.00/un (100un), custo2=4.00/un (100un) → custo_medio=3.00.
  - `test_reset_custo_estoque_zero` — estoque=0 antes da compra → custo_medio = custo da compra.
  - `test_reset_custo_estoque_negativo` — estoque=-5 → custo_medio = custo da compra (reset).
  - `test_criar_compra_gera_movimento` — verifica movimento ENTRADA no histórico.
  - `test_filtro_periodo_compras` — `data_inicio`/`data_fim` filtram corretamente.
  - `test_compra_item_inexistente` — 404 se item_id inválido.

- [ ] **G2.** `tests/test_estoque.py`:
  - `test_baixa_sem_venda_atualiza_saldo` — saldo reduzido, movimento SAIDA_PERDA criado.
  - `test_baixa_saldo_negativo_permitido` — saldo < 0 retornado, `saldo_negativo=True`.
  - `test_baixa_item_composto_bloqueado` — tipo=composto → 400.
  - `test_historico_ordenado_desc` — movimentos mais recentes primeiro.
  - `test_historico_filtro_tipo` — filtrar por tipo=entrada retorna só entradas.
  - `test_saldo_exclui_compostos` — GET /saldo não retorna itens compostos.
  - `test_saldo_filtro_busca` — filtro por nome parcial.

### Bloco H — Frontend: Sidebar + Rotas

- [ ] **H1.** `Sidebar.tsx` — adicionar antes do separador `─ Cadastros ─`:
  ```ts
  { label: "Compras", to: "/compras" },
  { label: "Estoque", to: "/estoque" },
  { label: "Histórico", to: "/estoque/movimentos" },
  ```

- [ ] **H2.** `App.tsx` — dentro do layout autenticado:
  ```tsx
  <Route path="/compras" element={<ComprasPage />} />
  <Route path="/compras/nova" element={<NovaCompraPage />} />
  <Route path="/estoque" element={<EstoquePage />} />
  <Route path="/estoque/movimentos" element={<MovimentosPage />} />
  ```

### Bloco I — Frontend: Compras

- [ ] **I1.** `compraSchemas.ts`:
  ```ts
  itemCompraSchema = z.object({
    item_id: z.number().int().positive(),
    quantidade: z.coerce.number().positive(),
    custo_total: z.coerce.number().positive(),
  })
  compraSchema = z.object({
    fornecedor_id: z.number().int().positive().optional(),
    data_compra: z.string().min(1),      // date ISO
    numero_nota: z.string().optional(),
    itens: z.array(itemCompraSchema).min(1, "Adicione ao menos 1 item"),
  })
  ```

- [ ] **I2.** `useCompras.ts`:
  - `useCompras(filters)` — useQuery `["compras", filters]`; GET /api/compras
  - `useCreateCompra()` — mutation POST /api/compras; onSuccess: invalidate + toast.success + navigate("/compras")

- [ ] **I3.** `ComprasPage.tsx`:
  - Filtros: data_inicio + data_fim (inputs date), select Fornecedor.
  - Lista: card por compra — data | fornecedor | nº nota | total | "Ver detalhes" link.
  - Total no período (Σ total das compras filtradas).
  - Botão "+ Nova Compra" → navigate("/compras/nova").

- [ ] **I4.** `NovaCompraPage.tsx` (página completa, não modal):
  - Campos cabeçalho: Fornecedor (select + botão "+ Cadastrar novo fornecedor" que abre inline mini-form → POST /api/fornecedores → adiciona à lista e seleciona), Data da compra (date input default hoje), Número da nota (opcional).
  - Linhas de itens com `useFieldArray`: select Item (todos os simples ativos via `/api/itens/simples`), input Quantidade, unidade (read-only do item), input Custo Total (R$), botão ✕.
  - Custo unitário calculado = custo_total / quantidade (display read-only por linha).
  - Total da compra = Σ custo_total (calculado no FE via useMemo).
  - Botão "+ Adicionar item".
  - Botões "Cancelar" (navigate back) e "Salvar Compra" (submit).

### Bloco J — Frontend: Estoque

- [ ] **J1.** `estoqueSchemas.ts`:
  ```ts
  baixaSemVendaSchema = z.object({
    item_id: z.number().int().positive("Selecione um item"),
    quantidade: z.coerce.number().positive("Quantidade deve ser > 0"),
    motivo: z.enum(["consumo_interno", "perda", "quebra", "cortesia", "outro"]),
    observacao: z.string().optional(),
  })
  ```

- [ ] **J2.** `useEstoque.ts`:
  - `useSaldoEstoque(filters)` — useQuery `["estoque", "saldo", filters]`; GET /api/estoque/saldo
  - `useBaixaSemVenda()` — mutation POST /api/estoque/baixa-sem-venda; onSuccess: toast (verde normal ou amarelo se saldo_negativo) + invalidate ["estoque"]
  - `useMovimentos(filters)` — useQuery `["estoque", "movimentos", filters]`; GET /api/estoque/movimentos

- [ ] **J3.** `EstoquePage.tsx`:
  - Filtros: select Categoria, input busca.
  - Tabela: Item | Categoria | Saldo (+ unidade) | Custo médio (formatCurrency/unidade ou "—").
  - Botão "Baixa Sem Venda" → abre `BaixaSemVendaModal`.
  - Só itens simples (backend já filtra).

- [ ] **J4.** `BaixaSemVendaModal.tsx`:
  - Select item (GET /api/estoque/saldo para mostrar saldo atual ao lado do nome).
  - Input quantidade.
  - Radio motivo: Consumo interno | Quebra/perda | Cortesia | Outro.
  - Textarea observação (opcional).
  - Ao salvar: se `saldo_negativo=true` → `toast.warning("Estoque ficou negativo")`.

- [ ] **J5.** `MovimentosPage.tsx`:
  - Filtros: select Item (todos simples), select Tipo (Todos/Entrada/Saída venda/Baixa), inputs data período.
  - Paginação simples: botões "← Anterior" / "Próximo →" + indicador "Página X".
  - Tabela: Data | Item | Tipo (badge colorido) | Quantidade | Saldo após.
  - Tipos com cores: entrada=verde, saida_venda=azul, saida_perda=laranja.

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

## Critérios de Aceite (do Issue #5)

- [ ] Schemas: `compras`, `itens_compra`, `movimento_estoque`.
- [ ] `POST /api/compras`: cria compra, gera movimentos de entrada, recalcula custo_medio ponderado.
- [ ] Reset custo_medio quando `estoque_anterior <= 0`.
- [ ] `GET /api/compras` com filtros período e fornecedor.
- [ ] `GET /api/estoque/saldo` — só itens simples, com filtros.
- [ ] `POST /api/estoque/baixa-sem-venda` — motivo enum, observação, gera `saida_perda`.
- [ ] `GET /api/estoque/movimentos` — paginado, filtros, ordenado por created_at DESC.
- [ ] Saldo negativo permitido; FE mostra toast amarelo.
- [ ] Cadastro inline de fornecedor no form Nova Compra.
- [ ] Testes: custo médio N compras, reset estoque ≤ 0, baixa sem venda, histórico desc.

---

## Notas Importantes

- **Enum storage:** `native_enum=False` em todos os Enums SQLAlchemy — compatibilidade SQLite nos testes.
- **Decimal:** usar `decimal.Decimal` nos models; response serializa como float via JSON.
- **custo_unitario derivado:** não é input do usuário — calculado como `custo_total / quantidade` no service.
- **saldo_apos:** campo desnormalizado no movimento — snapshot do saldo no momento do movimento. Essencial para histórico retroativo.
- **Compostos fora do saldo:** `GET /api/estoque/saldo` retorna apenas `tipo=simples`. Compostos dependem dos insumos.
- **Inline fornecedor:** FE cria fornecedor via `POST /api/fornecedores` (endpoint já existe do Issue #3), recebe o ID e popula o select.
- **Total compra:** calculado no service como Σ `custo_total` dos itens; gravado em `compras.total`.
- **Paginação movimentos:** `pagina` 1-indexed; `por_pagina` default 50; response inclui `total` para FE calcular páginas.
- **Toast saldo negativo:** usar `toast.warning()` do sonner (não `toast.error`) — saldo negativo não é erro de domínio.
- **Python 3.9:** `Optional[X]` não `X | None`, `list[X]` não `List[X]`.

---

## Tabela de Decisões

| Decisão | Valor | Motivo |
|---|---|---|
| Enum storage | `native_enum=False` (VARCHAR) | Compatibilidade SQLite nos testes |
| custo_unitario | derivado (custo_total/qtd) | Usuário pensa em valor total da linha, não por unidade |
| saldo_apos | desnormalizado no movimento | Histórico retroativo sem recalcular toda a série |
| Compostos no saldo | excluídos | Compostos não têm estoque físico próprio |
| Saldo negativo | permitido + toast amarelo | Realidade operacional (ruptura temporária) |
| Nova Compra | página completa (/compras/nova) | Form complexo (cabeçalho + N linhas) não cabe em modal |
| Inline fornecedor | POST /api/fornecedores existente | Reutiliza endpoint sem duplicar lógica |
| Paginação movimentos | limit/offset client-side | Volume cresce com tempo; 50/página é suficiente para MVP |

---

## Próximos Passos Pós-Conclusão

Issue #6 (Comandas) consome:
- `movimentos_estoque` → saida_venda gerada no fechamento (Issue #7).
- `itens.estoque_atual` → verificado no lançamento de item em comanda.
- `itens.custo_medio` → base para CMV no relatório.
- `itens.preco_venda` → snapshot em `itens_comanda.preco_unitario`.
