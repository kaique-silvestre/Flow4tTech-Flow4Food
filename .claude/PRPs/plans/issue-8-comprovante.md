# PRP — Issue #8: Comprovante + impressão via navegador

**Parent PRD:** `docs/prd_matchpoint_mvp.md`
**Parent Issue:** `docs/issues_matchpoint_mvp.md` → Issue 8
**Documento mestre:** `docs/matchpoint_documentacao.md` §8.3.7
**Type:** AFK
**Status:** Concluída ✓ (2026-05-07)
**Criado em:** 2026-05-07
**Depende de:** Issue #7 (Fechamento) — concluída

---

## Objetivo

Tela de comprovante pós-fechamento (§8.3.7). Cobre:
- `GET /api/comandas/{id}/comprovante` — payload formatado com dados do estabelecimento, itens, desconto, total, pagamentos.
- Tabela `estabelecimento` (id, nome, cnpj, endereco, telefone) — linha única com fallbacks se vazia.
- FE: rota `/comprovante/:id` **fora do AppLayout** (layout limpo para impressão), largura ~80mm.
- CSS `@media print` oculta sidebar, topbar e botões de ação.
- Botão `[IMPRIMIR]` → `window.print()`.
- Botão `[VOLTAR ÀS COMANDAS]` → navigate `/comandas`.
- Texto `*** NÃO É CUPOM FISCAL ***` sempre visível.
- Mostra: itens (nome, quantidade, cortesia flag, subtotal), desconto, total, pagamentos por método.
- `useFechamento.ts`: após fechamento total bem-sucedido, navegar para `/comprovante/:id` (não mais `/comandas`).

---

## Estrutura de Arquivos a Criar/Modificar

```
backend/
  alembic/versions/
    0008_estabelecimento.py                 # migration: tabela estabelecimento

  src/
    models/
      __init__.py                           # (modificar) importar Estabelecimento
      estabelecimento.py                    # Estabelecimento model

    schemas/
      comprovante.py                        # EstabelecimentoInfo, ItemComprovanteRow,
                                            # ComprovanteResponse

    repositories/
      estabelecimento_repository.py         # get_estabelecimento() -> Optional[Estabelecimento]

    services/
      comprovante_service.py                # build_comprovante(db, comanda_id) -> ComprovanteResponse

    api/
      routes/
        comandas.py                         # (modificar) GET /{comanda_id}/comprovante

  tests/
    test_comprovante.py                     # 4 testes

frontend/
  src/
    App.tsx                                 # (modificar) rota /comprovante/:id fora do AppLayout
    features/
      comandas/
        useComprovante.ts                   # useComprovante(id) query hook
        ComprovantePage.tsx                 # tela de comprovante com print CSS
        useFechamento.ts                    # (modificar) navigate para /comprovante/:id
```

---

## Modelo de Dados

### Tabela `estabelecimento` (nova)

```sql
estabelecimento (
  id       INTEGER PRIMARY KEY,
  nome     VARCHAR(200) NOT NULL DEFAULT 'Estabelecimento',
  cnpj     VARCHAR(20),
  endereco VARCHAR(300),
  telefone VARCHAR(30)
)
```

Linha única (id=1). Não inserida automaticamente na migration — fallbacks no service se não existir.

---

## Tarefas

### Bloco A — Migration

- [x] **A1.** `alembic/versions/0008_estabelecimento.py`:
  - `down_revision = "0007_fechamento"`.
  - `upgrade()`: `op.create_table("estabelecimento", ...)` com id, nome (default 'Estabelecimento'), cnpj, endereco, telefone.
  - `downgrade()`: `op.drop_table("estabelecimento")`.

### Bloco B — Model

- [x] **B1.** `models/estabelecimento.py`:
  ```python
  class Estabelecimento(Base):
      __tablename__ = "estabelecimento"
      id: Mapped[int] = mapped_column(primary_key=True)
      nome: Mapped[str] = mapped_column(sa.String(200), nullable=False, default="Estabelecimento")
      cnpj: Mapped[Optional[str]] = mapped_column(sa.String(20), nullable=True)
      endereco: Mapped[Optional[str]] = mapped_column(sa.String(300), nullable=True)
      telefone: Mapped[Optional[str]] = mapped_column(sa.String(30), nullable=True)
  ```

- [x] **B2.** `models/__init__.py` — importar `Estabelecimento`.

### Bloco C — Schemas

- [x] **C1.** `schemas/comprovante.py`:
  ```python
  class EstabelecimentoInfo(BaseModel):
      nome: str
      cnpj: Optional[str]
      endereco: Optional[str]
      telefone: Optional[str]

  class ItemComprovanteRow(BaseModel):
      nome: str
      quantidade: Decimal
      preco_unitario: Decimal
      subtotal: Decimal
      cortesia: bool

  class PagamentoComprovanteRow(BaseModel):
      metodo_nome: str
      valor: Decimal

  class ComprovanteResponse(BaseModel):
      comanda_id: int
      identificacao: str
      tipo_identificacao: str
      garcom_nome: str
      data_fechamento: Optional[datetime.datetime]
      estabelecimento: EstabelecimentoInfo
      itens: list[ItemComprovanteRow]
      subtotal: Decimal
      desconto_percentual: Optional[Decimal]
      desconto_valor: Optional[Decimal]
      total: Optional[Decimal]
      pagamentos: list[PagamentoComprovanteRow]
  ```

### Bloco D — Repository

- [x] **D1.** `repositories/estabelecimento_repository.py`:
  ```python
  def get_estabelecimento(db) -> Optional[Estabelecimento]:
      return db.get(Estabelecimento, 1)
  ```

### Bloco E — Service

- [x] **E1.** `services/comprovante_service.py`:
  ```python
  def build_comprovante(db, comanda_id: int) -> ComprovanteResponse:
      from src.repositories import comandas_repository, pagamentos_repository, estabelecimento_repository

      comanda = comandas_repository.get_by_id(db, comanda_id)
      if comanda is None:
          raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)

      estab = estabelecimento_repository.get_estabelecimento(db)
      estab_info = EstabelecimentoInfo(
          nome=estab.nome if estab else "Estabelecimento",
          cnpj=estab.cnpj if estab else None,
          endereco=estab.endereco if estab else None,
          telefone=estab.telefone if estab else None,
      )

      # Itens não cancelados
      itens_db = [i for i in comanda.itens if not i.cancelado]
      itens_rows = [
          ItemComprovanteRow(
              nome=i.item_nome,
              quantidade=i.quantidade,
              preco_unitario=i.preco_unitario,
              subtotal=i.subtotal,
              cortesia=i.cortesia,
          )
          for i in itens_db
      ]
      subtotal = sum(i.subtotal for i in itens_rows)

      pagamentos_db = pagamentos_repository.list_by_comanda(db, comanda_id)
      pagamentos_rows = [
          PagamentoComprovanteRow(
              metodo_nome=db.get(MetodoPagamento, p.metodo_id).nome,
              valor=p.valor,
          )
          for p in pagamentos_db
      ]

      garcom = db.get(Garcom, comanda.garcom_id)
      garcom_nome = garcom.nome if garcom else "—"

      return ComprovanteResponse(
          comanda_id=comanda.id,
          identificacao=comanda.identificacao,
          tipo_identificacao=comanda.tipo_identificacao,
          garcom_nome=garcom_nome,
          data_fechamento=comanda.data_fechamento,
          estabelecimento=estab_info,
          itens=itens_rows,
          subtotal=subtotal,
          desconto_percentual=comanda.desconto_percentual,
          desconto_valor=comanda.desconto_valor,
          total=comanda.total,
          pagamentos=pagamentos_rows,
      )
  ```

### Bloco F — Route

- [x] **F1.** `api/routes/comandas.py` — adicionar endpoint:
  ```python
  @router.get("/{comanda_id}/comprovante", response_model=ComprovanteResponse)
  def get_comprovante(comanda_id: int, db=Depends(get_db), _=Depends(get_current_user)):
      return comprovante_service.build_comprovante(db, comanda_id)
  ```

### Bloco G — Tests

- [x] **G1.** `tests/test_comprovante.py` (4 testes):
  - `test_comprovante_comanda_fechada` — comanda fechada retorna 200 com itens, subtotal, total, pagamentos.
  - `test_comprovante_sem_estabelecimento_usa_fallback` — sem linha em estabelecimento → nome="Estabelecimento".
  - `test_comprovante_com_estabelecimento` — com linha em estabelecimento → nome correto.
  - `test_comprovante_comanda_inexistente_retorna_404` — id inválido → 404.

### Bloco H — Frontend: useFechamento

- [x] **H1.** `features/comandas/useFechamento.ts` — atualizar `onSuccess`:
  ```ts
  if (data.status === "fechada") {
    toast.success("Comanda fechada com sucesso");
    navigate(`/comprovante/${comanda_id}`);  // era: navigate("/comandas")
  }
  ```

### Bloco I — Frontend: useComprovante

- [x] **I1.** `features/comandas/useComprovante.ts`:
  ```ts
  export function useComprovante(id: number | string) {
    return useQuery<ComprovanteResponse>({
      queryKey: ["comprovante", id],
      queryFn: () => api.get<ComprovanteResponse>(`/api/comandas/${id}/comprovante`).then(r => r.data),
      enabled: !!id,
    });
  }
  ```
  Definir interface `ComprovanteResponse` localmente (ou importar de tipos compartilhados).

### Bloco J — Frontend: ComprovantePage

- [x] **J1.** `features/comandas/ComprovantePage.tsx`:
  - **Layout**: div central largura ~80mm (320px), fundo branco, fonte monospace.
  - **Header**: nome do estabelecimento (fallback "Estabelecimento"), CNPJ/endereço/telefone se existir.
  - **Info comanda**: data_fechamento formatada `dd/mm/aaaa HH:mm`, `Comanda #ID — identificacao`.
  - **Itens**: lista: `Nx Nome (cortesia)    R$ subtotal` — cortesia mostra `(cortesia)` e `R$ 0,00`.
  - **Rodapé financeiro**: Subtotal, Desconto (se houver), TOTAL em destaque.
  - **Pagamentos**: linha por método: `PIX: R$ 50,10`.
  - **"*** NÃO É CUPOM FISCAL ***"** sempre presente.
  - **Botões** (ocultos em `@media print`):
    - `[IMPRIMIR]` → `window.print()`.
    - `[VOLTAR ÀS COMANDAS]` → `navigate("/comandas")`.
  - Loading skeleton enquanto carrega.
  - Se comanda não encontrada (404), mostrar mensagem de erro.
  - CSS `@media print`:
    ```css
    @media print {
      .no-print { display: none !important; }
      body { background: white; }
    }
    ```
    Aplicar classe `no-print` nos botões.

### Bloco K — Frontend: App.tsx

- [x] **K1.** `App.tsx` — adicionar rota `/comprovante/:id` **fora do AppLayout** mas dentro de `RequireAuth`:
  ```tsx
  import { ComprovantePage } from "@/features/comandas/ComprovantePage";
  // ...
  <Route element={<RequireAuth />}>
    <Route path="/comprovante/:id" element={<ComprovantePage />} />
    <Route element={<AppLayout />}>
      {/* rotas existentes */}
    </Route>
  </Route>
  ```

---

## Validações

### Backend
```bash
cd backend
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m mypy src/
.venv/Scripts/python -m pytest tests/ -v
```

### Frontend
```bash
cd frontend
npm run type-check
npm run lint
npm run build
```

---

## Critérios de Aceite

- [x] Tabela `estabelecimento` criada na migration 0008.
- [x] `GET /api/comandas/{id}/comprovante` retorna 200 com payload completo.
- [x] Sem linha em `estabelecimento` → fallback "Estabelecimento" sem erro.
- [x] 404 para comanda inexistente.
- [x] FE: rota `/comprovante/:id` fora do AppLayout (sem sidebar/topbar na tela de comprovante).
- [x] Layout ~80mm centralizado, fonte monospace.
- [x] "*** NÃO É CUPOM FISCAL ***" visível.
- [x] Itens com cortesia exibem `(cortesia)` e `R$ 0,00`.
- [x] Desconto exibido apenas se presente.
- [x] Botões ocultos em `@media print`.
- [x] `[IMPRIMIR]` aciona `window.print()`.
- [x] `[VOLTAR ÀS COMANDAS]` navega para `/comandas`.
- [x] `useFechamento.ts` navega para `/comprovante/:id` após fechamento total.
- [x] Testes backend: 4 cenários passando.

---

## Notas Importantes

- **Rota fora do AppLayout**: `/comprovante/:id` deve estar em `<Route element={<RequireAuth />}>` mas **não** dentro de `<Route element={<AppLayout />}>`. Isso garante que sidebar e topbar não apareçam na página, tornando `@media print` mais simples.
- **Python 3.9**: `Optional[X]` não `X | None`.
- **`comanda.itens`**: ItemComanda tem `item_nome` (string snapshot), não precisar fazer join com `Item` para o comprovante.
- **`comanda.itens`** carregado via relationship na model — verificar se relationship já existe em `models/comandas.py`. Se não existir, carregar via query separada: `db.execute(select(ItemComanda).where(ItemComanda.comanda_id == comanda_id)).scalars().all()`.
- **Formato moeda**: usar `Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })` no FE.
- **Formato data**: usar `new Date(data_fechamento).toLocaleString('pt-BR')` no FE.
- **ErrorCode.NOT_FOUND**: já existe no projeto — importar de `src.core.errors`.
