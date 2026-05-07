# PRP — Issue #6: Comandas (abrir, lançar, editar, cancelar item, version conflict)

**Parent PRD:** `docs/prd_matchpoint_mvp.md`
**Parent Issue:** `docs/issues_matchpoint_mvp.md` → Issue 6
**Documento mestre:** `docs/matchpoint_documentacao.md` §8.3.1 a §8.3.5
**Type:** HITL (núcleo do sistema, concorrência, auditoria)
**Status:** Pronto para execução
**Criado em:** 2026-05-07
**Depende de:** Issue #4 (Itens) — concluída

---

## Objetivo

Tela mais usada do sistema. Cobre §8.3.1 a §8.3.5 (sem fechamento — Issue #7). Inclui:
- Controle otimista de concorrência via coluna `version` (mismatch → 409 COMANDA_DESATUALIZADA).
- Tabela de auditoria `eventos_comanda` — cada mutação grava um evento.
- Snapshot de preço no lançamento (`itens_comanda.preco_unitario`).
- Cortesia: `cortesia=True` → `preco_unitario=0`.
- Cancelamento de item com flag `estornado` (sem alterar estoque em Issue 6; estoque gerenciado no fechamento — Issue 7).
- Endpoint `GET /api/itens/top` (atalhos visuais da comanda).
- FE: lista de comandas, modal Nova Comanda, tela Comanda Aberta (split panel), modal Cancelar Item.

---

## Estrutura de Arquivos a Criar/Modificar

```
backend/
  alembic/versions/
    0006_comandas.py                        # migration: comandas, itens_comanda, eventos_comanda

  src/
    models/
      __init__.py                           # (modificar) importar 3 novos models
      comandas.py                           # Comanda, StatusComanda(enum)
      itens_comanda.py                      # ItemComanda, MotivoCancelamento(enum)
      eventos_comanda.py                    # EventoComanda, TipoEvento(enum)

    schemas/
      comandas.py                           # request/response schemas

    repositories/
      comandas_repository.py               # CRUD + version conflict

    services/
      comandas_service.py                  # domain logic + event log

    api/
      routes/
        comandas.py                        # todos os endpoints de comandas
        itens.py                           # (modificar) adicionar GET /top

    main.py                                # (modificar) registrar router comandas

  tests/
    test_comandas.py                       # snapshot preço, cortesia, 409, eventos

frontend/
  src/
    App.tsx                                # (modificar) rotas /comandas e /comandas/:id
    components/
      layout/
        Sidebar.tsx                        # (modificar) link Comandas

    features/
      comandas/
        comandaSchemas.ts                  # Zod schemas
        useComandas.ts                     # queries + mutations + 409 handler
        ComandasPage.tsx                   # lista de comandas abertas com busca
        NovaComandaModal.tsx               # modal: identificação, garçom, pessoas
        ComandaAbertaPage.tsx              # split: painel lançamento + painel itens
        CancelarItemModal.tsx              # modal: motivo + checkbox estornar
```

---

## Modelo de Dados

### Tabelas

```sql
comandas (
  id                INTEGER PRIMARY KEY,
  identificacao     VARCHAR(150) NOT NULL,
  tipo_identificacao VARCHAR(10) NOT NULL,  -- 'nome' | 'mesa'
  garcom_id         INTEGER NOT NULL REFERENCES garcons(id),
  status            VARCHAR(15) NOT NULL DEFAULT 'aberta',  -- aberta | fechada | cancelada
  version           INTEGER NOT NULL DEFAULT 1,
  pessoas           TEXT NULLABLE,          -- JSON array of names, e.g. '["João","Maria"]'
  created_at        TIMESTAMP NOT NULL DEFAULT now(),
  updated_at        TIMESTAMP NOT NULL DEFAULT now()
)

itens_comanda (
  id                INTEGER PRIMARY KEY,
  comanda_id        INTEGER NOT NULL REFERENCES comandas(id),
  item_id           INTEGER NOT NULL REFERENCES itens(id),
  quantidade        NUMERIC(10,3) NOT NULL,
  preco_unitario    NUMERIC(10,2) NOT NULL,  -- snapshot no lançamento; 0 se cortesia
  pessoa_associada  VARCHAR(100) NULLABLE,
  observacao        VARCHAR(300) NULLABLE,
  cortesia          BOOLEAN NOT NULL DEFAULT FALSE,
  cancelado         BOOLEAN NOT NULL DEFAULT FALSE,
  motivo_cancelamento VARCHAR(30) NULLABLE,
  estornado         BOOLEAN NOT NULL DEFAULT FALSE,  -- flag para Issue 7
  created_at        TIMESTAMP NOT NULL DEFAULT now()
)

eventos_comanda (
  id                INTEGER PRIMARY KEY,
  comanda_id        INTEGER NOT NULL REFERENCES comandas(id),
  tipo              VARCHAR(30) NOT NULL,
  payload           TEXT NULLABLE,          -- JSON string
  garcom_id         INTEGER NULLABLE REFERENCES garcons(id),
  created_at        TIMESTAMP NOT NULL DEFAULT now()
)
```

### Enums Python

```python
class StatusComanda(str, enum.Enum):
    ABERTA = "aberta"
    FECHADA = "fechada"
    CANCELADA = "cancelada"

class MotivoCancelamento(str, enum.Enum):
    CLIENTE_DESISTIU = "cliente_desistiu"
    ERRO_LANCAMENTO = "erro_lancamento"
    ITEM_INDISPONIVEL = "item_indisponivel"
    OUTRO = "outro"

class TipoEvento(str, enum.Enum):
    COMANDA_ABERTA = "comanda_aberta"
    ITEM_LANCADO = "item_lancado"
    ITEM_EDITADO = "item_editado"
    ITEM_CANCELADO = "item_cancelado"
```

---

## Tarefas

### Bloco A — Migration

- [ ] **A1.** `alembic/versions/0006_comandas.py`:
  - `down_revision = "0005_estoque_compras"`
  - `upgrade()`: criar `comandas`, `itens_comanda`, `eventos_comanda` (respeitar FKs).
  - `downgrade()`: drop na ordem inversa.

### Bloco B — Models

- [ ] **B1.** `models/comandas.py`:
  ```python
  class StatusComanda(str, enum.Enum): ABERTA="aberta"; FECHADA="fechada"; CANCELADA="cancelada"
  class Comanda(Base):
      __tablename__ = "comandas"
      id, identificacao(String 150), tipo_identificacao(String 10),
      garcom_id(FK NOT NULL), status(Enum native_enum=False default ABERTA),
      version(Integer NOT NULL default 1), pessoas(Text nullable),
      created_at(DateTime server_default), updated_at(DateTime server_default onupdate)
  ```

- [ ] **B2.** `models/itens_comanda.py`:
  ```python
  class MotivoCancelamento(str, enum.Enum): CLIENTE_DESISTIU | ERRO_LANCAMENTO | ITEM_INDISPONIVEL | OUTRO
  class ItemComanda(Base):
      __tablename__ = "itens_comanda"
      id, comanda_id(FK), item_id(FK), quantidade(Numeric 10,3),
      preco_unitario(Numeric 10,2), pessoa_associada(String 100 nullable),
      observacao(String 300 nullable), cortesia(bool default False),
      cancelado(bool default False), motivo_cancelamento(String 30 nullable),
      estornado(bool default False), created_at(DateTime server_default)
  ```

- [ ] **B3.** `models/eventos_comanda.py`:
  ```python
  class TipoEvento(str, enum.Enum): COMANDA_ABERTA | ITEM_LANCADO | ITEM_EDITADO | ITEM_CANCELADO
  class EventoComanda(Base):
      __tablename__ = "eventos_comanda"
      id, comanda_id(FK), tipo(String 30), payload(Text nullable),
      garcom_id(Integer FK nullable), created_at(DateTime server_default)
  ```

- [ ] **B4.** Importar 3 models em `models/__init__.py`.

### Bloco C — Schemas

- [ ] **C1.** `schemas/comandas.py`:
  - `ComandaCreateRequest(identificacao: str, tipo_identificacao: Literal["nome","mesa"], garcom_id: int, pessoas: list[str] = [])`.
  - `LancarItemRequest(item_id: int, quantidade: Decimal > 0, pessoa_associada?: str, observacao?: str, cortesia: bool = False)`.
  - `EditarItemRequest(quantidade?: Decimal > 0, pessoa_associada?: str, observacao?: str)`.
  - `CancelarItemRequest(motivo: MotivoCancelamento, estornado: bool = False)`.
  - `ItemComandaResponse(id, item_id, item_nome, quantidade, preco_unitario, subtotal, pessoa_associada, observacao, cortesia, cancelado, motivo_cancelamento, estornado, created_at)`.
    - `subtotal = quantidade × preco_unitario`.
  - `ComandaResponse(id, identificacao, tipo_identificacao, garcom_id, garcom_nome, status, version, pessoas: list[str], total_parcial, itens_ativos: list[ItemComandaResponse], created_at, tempo_aberta_minutos: int)`.
    - `total_parcial = Σ subtotal dos itens não cancelados (cortesia tem subtotal=0)`.
    - `tempo_aberta_minutos = (now - created_at).seconds // 60`.

### Bloco D — Repository

- [ ] **D1.** `repositories/comandas_repository.py`:
  - `create_comanda(db, data: ComandaCreateRequest) -> Comanda`.
  - `list_abertas(db, busca?) -> list[Comanda]` — só `status=aberta`, busca em `identificacao`.
  - `get_by_id(db, comanda_id) -> Optional[Comanda]`.
  - `increment_version(db, comanda_id, version_esperada) -> bool` — `UPDATE WHERE id=? AND version=?; return rowcount > 0`. Se False → 409.
  - `add_item(db, comanda_id, item_id, quantidade, preco_unitario, pessoa_associada, observacao, cortesia) -> ItemComanda`.
  - `get_item(db, item_id) -> Optional[ItemComanda]`.
  - `update_item(db, item_id, quantidade?, pessoa_associada?, observacao?) -> Optional[ItemComanda]`.
  - `cancelar_item(db, item_id, motivo, estornado) -> Optional[ItemComanda]`.
  - `get_itens_ativos(db, comanda_id) -> list[ItemComanda]`.
  - `add_evento(db, comanda_id, tipo, payload_dict?, garcom_id?) -> EventoComanda`.
  - `top_itens(db, dias, limit) -> list[tuple[int, int]]` — [(item_id, count)].

### Bloco E — Service

- [ ] **E1.** `services/comandas_service.py`:

  **`abrir_comanda(db, data)`:**
  - Buscar garçom; 404 se não existe.
  - Validar `garcom.ativo == True`; raise `AppError(GARCOM_INATIVO, ..., 400)` se não.
  - `create_comanda(db, data)`.
  - `add_evento(db, comanda.id, COMANDA_ABERTA, payload={identificacao, garcom_id})`.
  - `db.commit()`. Retornar `_build_response(db, comanda)`.

  **`get_comanda(db, comanda_id)`:**
  - `get_by_id`; 404 se None. Retornar `_build_response`.

  **`lancar_item(db, comanda_id, version, data)`:**
  - `get_by_id`; 404 se não existe. Verificar `status=aberta`; raise COMANDA_FECHADA se não.
  - Buscar item vendável; 404 se não existe ou `vendavel=False`.
  - `preco_unitario = 0 if data.cortesia else item.preco_venda` (None → 0).
  - `increment_version(db, comanda_id, version)` → se False: raise `AppError(COMANDA_DESATUALIZADA, ..., 409)`.
  - `add_item(...)`.
  - `add_evento(db, comanda_id, ITEM_LANCADO, {item_id, quantidade, cortesia, pessoa_associada})`.
  - `db.commit()`. Retornar `_build_response`.

  **`editar_item(db, comanda_id, item_comanda_id, version, data)`:**
  - Validar comanda aberta + item não cancelado.
  - `increment_version`; 409 se False.
  - `update_item(...)`.
  - `add_evento(db, comanda_id, ITEM_EDITADO, {item_comanda_id, ...alterações...})`.
  - `db.commit()`. Retornar `_build_response`.

  **`cancelar_item(db, comanda_id, item_comanda_id, version, data)`:**
  - Validar comanda aberta + item não já cancelado.
  - `increment_version`; 409 se False.
  - `cancelar_item_repo(db, item_comanda_id, data.motivo, data.estornado)`.
  - `add_evento(db, comanda_id, ITEM_CANCELADO, {item_comanda_id, motivo, estornado})`.
  - `db.commit()`. Retornar `_build_response`.

  **`_build_response(db, comanda) -> ComandaResponse`:**
  - Buscar garçom nome.
  - Parsear `pessoas` de JSON.
  - `get_itens_ativos(db, comanda.id)` — todos, inclusive cancelados (FE decide como exibir).
  - Calcular `total_parcial` e `tempo_aberta_minutos`.

  **`get_top_itens(db, dias, limit) -> list[ItemResponse]`:**
  - `top_itens(db, dias, limit)` → lista de item_id.
  - Para cada item_id: buscar Item e retornar ItemResponse via `itens_service._build_response`.

### Bloco F — Routes

- [ ] **F1.** `api/routes/comandas.py`:
  - `POST /api/comandas` → 201 + ComandaResponse.
  - `GET /api/comandas` — query param: `busca?` (status=aberta implícito).
  - `GET /api/comandas/{id}` → ComandaResponse.
  - `POST /api/comandas/{id}/itens` — header ou body `version` (int).
  - `PATCH /api/comandas/{id}/itens/{item_id}` — body inclui `version`.
  - `POST /api/comandas/{id}/itens/{item_id}/cancelar` — body inclui `version`.
  - Todas: `Depends(get_current_user)`.

  **Nota sobre version**: incluir `version` no body dos requests de mutação (não header — mais simples com FastAPI/Pydantic).

- [ ] **F2.** `api/routes/itens.py` — adicionar:
  - `GET /api/itens/top?dias=7&limit=6` → `list[ItemResponse]`.
  - **ATENÇÃO**: esta rota deve ser registrada ANTES de `GET /api/itens/{id}` para evitar conflito de path.

- [ ] **F3.** `main.py` — adicionar:
  ```python
  app.include_router(comandas_routes.router, prefix="/api/comandas", tags=["comandas"])
  ```

### Bloco G — Tests

- [ ] **G1.** `tests/test_comandas.py`:
  - `test_abrir_comanda` — cria comanda, verifica status=aberta, versão=1.
  - `test_garcom_inativo_bloqueado` — garçom ativo=False → 400 GARCOM_INATIVO.
  - `test_lancar_item_snapshot_preco` — preco_unitario = item.preco_venda no momento do lançamento.
  - `test_cortesia_preco_zero` — cortesia=True → preco_unitario=0, subtotal=0.
  - `test_lancar_incrementa_version` — version vai de 1 para 2.
  - `test_version_conflict_retorna_409` — enviar version errada → 409 COMANDA_DESATUALIZADA.
  - `test_editar_item` — alterar quantidade e pessoa_associada.
  - `test_cancelar_item` — item marcado cancelado, não aparece no total_parcial.
  - `test_eventos_gravados` — após abrir + lançar: 2 eventos em eventos_comanda.
  - `test_total_parcial_exclui_cancelados_e_cortesias` — total correto.
  - `test_top_itens` — lançar item 3x → aparece no top.

### Bloco H — Frontend: Sidebar + Rotas

- [ ] **H1.** `Sidebar.tsx` — adicionar link `{ label: "Comandas", to: "/comandas" }` (já existe como placeholder, mudar para rota real ou confirmar).
- [ ] **H2.** `App.tsx`:
  ```tsx
  <Route path="/comandas" element={<ComandasPage />} />
  <Route path="/comandas/:id" element={<ComandaAbertaPage />} />
  ```

### Bloco I — Frontend: Feature Comandas

- [ ] **I1.** `comandaSchemas.ts`:
  ```ts
  novaComandaSchema = z.object({
    identificacao: z.string().min(1),
    tipo_identificacao: z.enum(["nome", "mesa"]),
    garcom_id: z.number().int().positive("Selecione um garçom"),
    pessoas: z.array(z.string().min(1)).default([]),
  })
  lancarItemSchema = z.object({
    item_id: z.number().int().positive(),
    quantidade: z.coerce.number().positive(),
    pessoa_associada: z.string().optional(),
    observacao: z.string().optional(),
    cortesia: z.boolean().default(false),
  })
  cancelarItemSchema = z.object({
    motivo: z.enum(["cliente_desistiu","erro_lancamento","item_indisponivel","outro"]),
    estornado: z.boolean().default(false),
  })
  ```

- [ ] **I2.** `useComandas.ts`:
  - `useComandas(busca?)` — useQuery `["comandas", busca]`; GET /api/comandas.
  - `useComanda(id)` — useQuery `["comandas", id]`; GET /api/comandas/:id.
  - `useAbrirComanda()` — mutation; onSuccess: navigate /comandas/:id + invalidate.
  - `useLancarItem(comanda_id)` — mutation; **onError 409**: `toast.error("Comanda alterada por outro usuário, recarregue")` + `qc.invalidateQueries(["comandas", comanda_id])`.
  - `useEditarItem(comanda_id)` — mutation; mesmo 409 handler.
  - `useCancelarItem(comanda_id)` — mutation; mesmo 409 handler.
  - `useTopItens(dias?, limit?)` — useQuery `["itens", "top", {dias, limit}]`; GET /api/itens/top.

- [ ] **I3.** `ComandasPage.tsx`:
  - Input busca (debounce 300ms ou onChange direto).
  - Lista de cards: identificação, garçom, qtd itens, total parcial, tempo aberta.
  - Botão "Abrir comanda" → navigate(`/comandas/${id}`).
  - Botão "+ Nova Comanda" → abre `NovaComandaModal`.
  - Loading skeleton 3 cards.

- [ ] **I4.** `NovaComandaModal.tsx`:
  - Radio: Nome do responsável | Número da mesa.
  - Input identificação.
  - Select garçom (só ativos — filtrar no FE de `useGarcons()`).
  - Campo "Pessoas": input + botão "Adicionar" → lista de chips removíveis.
  - Submit → `useAbrirComanda()` → onSuccess fecha modal.

- [ ] **I5.** `ComandaAbertaPage.tsx` (layout split):
  - **Header**: `#ID — IDENTIFICAÇÃO`, garçom, tempo aberta.
  - **Painel esquerdo — Adicionar Item:**
    - Input busca com `useItens({ busca, vendavel: true })` — debounce 300ms.
    - Grid 2×3 de atalhos (`useTopItens(7, 6)`).
    - Item selecionado: mostra nome + preço.
    - Inputs: quantidade (default 1), pessoa (radio baseado em `comanda.pessoas`), observação, checkbox cortesia.
    - Botão "+ Adicionar Item" → `useLancarItem`.
  - **Painel direito — Itens Lançados:**
    - Lista de `itens_ativos` não cancelados.
    - Cada linha: qtd × nome, pessoa, obs, preço/subtotal, badges (🎁 cortesia).
    - Botão "Editar" → inline edit (quantidade + pessoa + obs) + salvar.
    - Botão "✕" → abre `CancelarItemModal`.
    - Rodapé: subtotal.
  - Usar `useComanda(id)` com refetch em 409.

- [ ] **I6.** `CancelarItemModal.tsx`:
  - Select motivo: Cliente desistiu | Erro de lançamento | Item indisponível | Outro.
  - Checkbox "Estornar itens ao estoque".
  - Submit → `useCancelarItem`.

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

## Critérios de Aceite (do Issue #6)

- [ ] Schemas: `comandas` (com `version`), `itens_comanda`, `eventos_comanda`.
- [ ] POST /api/comandas: valida garçom ativo, cria comanda, grava evento.
- [ ] GET /api/comandas?busca=: filtra comandas abertas.
- [ ] POST itens: snapshot preco_venda, cortesia→0, incrementa version, grava evento.
- [ ] PATCH itens: edita, incrementa version, grava evento.
- [ ] POST cancelar: marca cancelado, grava evento, version conflict 409.
- [ ] GET /api/itens/top: top itens por frequência no período.
- [ ] 409 COMANDA_DESATUALIZADA se version != esperada.
- [ ] total_parcial exclui cancelados e cortesias.
- [ ] FE trata 409: toast + refetch.
- [ ] Testes: snapshot, cortesia, 409, eventos.

---

## Notas Importantes

- **version conflict**: usar `UPDATE WHERE id=? AND version=?` + verificar `rowcount`. NÃO usar SELECT + compare + UPDATE (race condition).
- **Enum storage**: `native_enum=False` em todos os Enums SQLAlchemy.
- **pessoas field**: JSON text no banco (`json.dumps(list)` / `json.loads(str)`). Exposto como `list[str]` na API.
- **GET /api/itens/top**: registrar rota `/top` ANTES de `/{id}` no router de itens para evitar conflito.
- **preco_unitario snapshot**: usar `item.preco_venda or Decimal("0")` — item sem preço configurado tem subtotal 0.
- **itens_ativos no response**: retornar TODOS os itens (incluindo cancelados) — FE usa `cancelado=True` para exibir riscado ou não exibir.
- **Edição não baixa estoque**: Issue 6 não modifica `itens.estoque_atual`. Estoque gerenciado no fechamento (Issue 7).
- **`updated_at` em Comanda**: atualizado a cada `increment_version`. Usar `onupdate=func.now()` no SQLAlchemy.
- **Python 3.9**: `Optional[X]` não `X | None`, `list[X]` não `List[X]`.
- **`version` no body**: incluir `version: int` nos requests de mutação (LancarItemRequest, EditarItemRequest, CancelarItemRequest) — mais explícito e simples.

---

## Tabela de Decisões

| Decisão | Valor | Motivo |
|---|---|---|
| version no body | sim (não header) | Mais simples com FastAPI/Pydantic; sem config especial |
| pessoas como JSON text | TEXT com json.dumps/loads | SQLite sem JSONB; lista simples de nomes |
| itens cancelados no response | incluídos (cancelado=True) | FE filtra; histórico visível na tela |
| estornar_estoque em Issue 6 | só salva flag, sem tocar estoque | Estoque gerenciado no fechamento (Issue 7) |
| UPDATE com rowcount | SELECT + check | Atômico, sem race condition |
| /itens/top antes de /{id} | ordem de registro no router | FastAPI match por ordem; `/top` seria capturado por `/{id}` |
| busca vendavel=True | apenas vendáveis no lançamento | Não faz sentido lançar insumo não-vendável |

---

## Próximos Passos Pós-Conclusão

Issue #7 (Fechamento) consome:
- `itens_comanda.preco_unitario` → cálculo subtotal.
- `itens_comanda.cancelado` → excluir do total.
- `itens_comanda.cortesia` → excluir da receita, incluir no CMV.
- `itens_comanda.estornado` → pular na baixa de estoque.
- `comandas.version` → mantido para concorrência no fechamento.
- `comandas.status` → mudado para 'fechada' no fechamento.
- `movimentos_estoque` → criados no fechamento (saida_venda por item).
