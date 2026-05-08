# PRP â€” Issue #7: Fechamento de comanda (desconto, divisÃ£o, pagamento misto, parcial, baixa de estoque)

**Parent PRD:** `docs/prd_matchpoint_mvp.md`
**Parent Issue:** `docs/issues_matchpoint_mvp.md` â†’ Issue 7
**Documento mestre:** `docs/matchpoint_documentacao.md` Â§8.3.6 + Â§10.3
**Type:** HITL (operaÃ§Ã£o crÃ­tica, atomicidade)
**Status:** Pronto para execuÃ§Ã£o
**Criado em:** 2026-05-07
**Depende de:** Issue #5 (Estoque & Compras) + Issue #6 (Comandas) â€” concluÃ­das

---

## Objetivo

OperaÃ§Ã£o mais crÃ­tica do sistema. Cobre Â§8.3.6. Inclui:
- `POST /api/comandas/{id}/desconto` â€” aplica desconto (percentual ou valor fixo) na comanda.
- `POST /api/comandas/{id}/fechar` â€” fecha comanda com lista de pagamentos, modo de divisÃ£o, flag parcial.
- ValidaÃ§Ã£o: soma pagamentos = total Â±0,01 (cÃ³digo `PAGAMENTO_NAO_BATE`).
- ValidaÃ§Ã£o: modo "por_pessoa" exige â‰¥ 2 pessoas (cÃ³digo `PESSOAS_INSUFICIENTES`).
- Pagamento parcial: comanda volta `aberta` com `saldo_pendente` deduzido; calculado sobre **subtotal sem desconto**.
- TransaÃ§Ã£o atÃ´mica: pagamentos + status `fechada` + baixa de estoque (explode ficha tÃ©cnica em compostos).
- Cortesia entra no CMV (baixa de estoque Ã© registrada) mas nÃ£o em receita (preco_unitario=0 nÃ£o soma subtotal).
- Saldo negativo de estoque permitido; lista de insumos negativos retornada na resposta.
- FE: modal Aplicar Desconto, tela Fechamento (4 modos, pagamento misto), navegaÃ§Ã£o pÃ³s-fechamento para comprovante.

---

## Estrutura de Arquivos a Criar/Modificar

```
backend/
  alembic/versions/
    0007_fechamento.py                      # migration: tabela pagamentos + colunas em comandas

  src/
    models/
      __init__.py                           # (modificar) importar Pagamento
      pagamentos.py                         # Pagamento model

    schemas/
      fechamento.py                         # AplicarDescontoRequest, PagamentoRequest,
                                            # FecharComandaRequest, PagamentoResponse
      comandas.py                           # (modificar) ComandaResponse: + desconto, total,
                                            # saldo_pendente, data_fechamento, pagamentos

    repositories/
      pagamentos_repository.py             # create_pagamento, list_by_comanda
      comandas_repository.py               # (modificar) fechar_comanda, atualizar_desconto,
                                            # atualizar_saldo_pendente

    services/
      comandas_service.py                  # (modificar) aplicar_desconto, fechar_comanda,
                                            # _dar_baixa_estoque, _build_response (+ pagamentos)

    api/
      routes/
        comandas.py                        # (modificar) 2 novos endpoints

  tests/
    test_fechamento.py                     # 10 testes (subtotal, desconto, pagamento, parcial,
                                            # divisÃ£o, explosÃ£o ficha, atomicidade, CMV cortesia)

frontend/
  src/
    App.tsx                                # (modificar) rota /comandas/:id/fechar
    features/
      comandas/
        fechamentoSchemas.ts               # Zod schemas (desconto, fechar)
        useFechamento.ts                   # useAplicarDesconto, useFecharComanda
        FechamentoPage.tsx                 # tela completa de fechamento
        AplicarDescontoModal.tsx           # modal: radio percentual|valor fixo + input
        ComandaAbertaPage.tsx              # (modificar) botÃ£o [FECHAR CONTA]
```

---

## Modelo de Dados

### Tabela `pagamentos` (nova)

```sql
pagamentos (
  id          INTEGER PRIMARY KEY,
  comanda_id  INTEGER NOT NULL REFERENCES comandas(id),
  metodo_id   INTEGER NOT NULL REFERENCES metodos_pagamento(id),
  valor       NUMERIC(10,2) NOT NULL,
  created_at  TIMESTAMP NOT NULL DEFAULT now()
)
```

### Colunas novas em `comandas`

```sql
ALTER TABLE comandas ADD COLUMN desconto_percentual NUMERIC(5,2) DEFAULT NULL;
ALTER TABLE comandas ADD COLUMN desconto_valor      NUMERIC(10,2) DEFAULT NULL;
ALTER TABLE comandas ADD COLUMN total               NUMERIC(10,2) DEFAULT NULL;
ALTER TABLE comandas ADD COLUMN saldo_pendente      NUMERIC(10,2) DEFAULT NULL;
ALTER TABLE comandas ADD COLUMN data_fechamento     DATETIME DEFAULT NULL;
```

---

## Tarefas

### Bloco A â€” Migration

- [x] **A1.** `alembic/versions/0007_fechamento.py`:
  - `down_revision = "0006_comandas"`.
  - `upgrade()`:
    - `op.add_column("comandas", sa.Column("desconto_percentual", sa.Numeric(5,2), nullable=True))`
    - `op.add_column("comandas", sa.Column("desconto_valor", sa.Numeric(10,2), nullable=True))`
    - `op.add_column("comandas", sa.Column("total", sa.Numeric(10,2), nullable=True))`
    - `op.add_column("comandas", sa.Column("saldo_pendente", sa.Numeric(10,2), nullable=True))`
    - `op.add_column("comandas", sa.Column("data_fechamento", sa.DateTime(), nullable=True))`
    - `op.create_table("pagamentos", ...)` com id, comanda_id FK, metodo_id FK, valor, created_at.
  - `downgrade()`: drop table + drop columns (ordem inversa).

### Bloco B â€” Models

- [x] **B1.** `models/pagamentos.py`:
  ```python
  class Pagamento(Base):
      __tablename__ = "pagamentos"
      id: Mapped[int] = mapped_column(primary_key=True)
      comanda_id: Mapped[int] = mapped_column(sa.ForeignKey("comandas.id"), nullable=False)
      metodo_id: Mapped[int] = mapped_column(sa.ForeignKey("metodos_pagamento.id"), nullable=False)
      valor: Mapped[Decimal] = mapped_column(sa.Numeric(10,2), nullable=False)
      created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=sa.func.now())
  ```

- [x] **B2.** `models/comandas.py` â€” adicionar 5 colunas:
  ```python
  desconto_percentual: Mapped[Optional[Decimal]] = mapped_column(sa.Numeric(5,2), nullable=True)
  desconto_valor: Mapped[Optional[Decimal]] = mapped_column(sa.Numeric(10,2), nullable=True)
  total: Mapped[Optional[Decimal]] = mapped_column(sa.Numeric(10,2), nullable=True)
  saldo_pendente: Mapped[Optional[Decimal]] = mapped_column(sa.Numeric(10,2), nullable=True)
  data_fechamento: Mapped[Optional[datetime.datetime]] = mapped_column(nullable=True)
  ```

- [x] **B3.** `models/__init__.py` â€” importar `Pagamento`.

### Bloco C â€” Schemas

- [x] **C1.** `schemas/fechamento.py`:
  ```python
  class AplicarDescontoRequest(BaseModel):
      desconto_percentual: Optional[Decimal] = Field(None, ge=0, le=100)
      desconto_valor: Optional[Decimal] = Field(None, ge=0)
      # Validar: exatamente um dos dois informado (validator)

  class PagamentoRequest(BaseModel):
      metodo_id: int
      valor: Decimal = Field(..., gt=0)

  class FecharComandaRequest(BaseModel):
      pagamentos: list[PagamentoRequest]
      modo_divisao: Literal["sem_divisao", "igualmente", "por_pessoa", "parcial"]
      # Nota: pagamento_parcial = (modo_divisao == "parcial")
  ```

- [x] **C2.** `schemas/fechamento.py` â€” adicionar response:
  ```python
  class PagamentoResponse(BaseModel):
      model_config = ConfigDict(from_attributes=True)
      id: int
      metodo_id: int
      metodo_nome: str
      valor: Decimal
  ```

- [x] **C3.** `schemas/comandas.py` â€” extender `ComandaResponse`:
  ```python
  # Adicionar campos ao ComandaResponse existente:
  desconto_percentual: Optional[Decimal]
  desconto_valor: Optional[Decimal]
  total: Optional[Decimal]
  saldo_pendente: Optional[Decimal]
  data_fechamento: Optional[datetime.datetime]
  pagamentos: list[PagamentoResponse]
  itens_negativos: list[str]   # nomes dos insumos que ficaram com saldo negativo pÃ³s-fechamento
  ```

### Bloco D â€” Repository

- [x] **D1.** `repositories/pagamentos_repository.py`:
  ```python
  def create_pagamento(db, comanda_id, metodo_id, valor) -> Pagamento
  def list_by_comanda(db, comanda_id) -> list[Pagamento]
  ```

- [x] **D2.** `repositories/comandas_repository.py` â€” adicionar:
  ```python
  def atualizar_desconto(db, comanda_id, desconto_percentual, desconto_valor) -> None
      # UPDATE comandas SET desconto_percentual=?, desconto_valor=? WHERE id=?

  def fechar_comanda_repo(db, comanda_id, total) -> None
      # UPDATE SET status='fechada', total=total, data_fechamento=now() WHERE id=?

  def atualizar_saldo_pendente(db, comanda_id, saldo) -> None
      # UPDATE SET saldo_pendente=saldo WHERE id=?

  def get_itens_para_fechar(db, comanda_id) -> list[ItemComanda]
      # Retorna todos os itens NÃƒO cancelados (incluindo cortesias)
  ```

### Bloco E â€” Service

- [x] **E1.** `services/comandas_service.py` â€” adicionar `aplicar_desconto`:
  ```python
  def aplicar_desconto(db, comanda_id, data: AplicarDescontoRequest) -> ComandaResponse:
      comanda = get_by_id(db, comanda_id); 404 se None
      se comanda.status != 'aberta': raise AppError(COMANDA_FECHADA, ..., 400)
      atualizar_desconto(db, comanda_id, data.desconto_percentual, data.desconto_valor)
      db.commit()
      return _build_response(db, comanda)
  ```

- [x] **E2.** `services/comandas_service.py` â€” adicionar `fechar_comanda`:
  ```python
  def fechar_comanda(db, comanda_id, data: FecharComandaRequest) -> ComandaResponse:
      comanda = get_by_id(db, comanda_id); 404 se None
      se comanda.status != 'aberta': raise AppError(COMANDA_FECHADA, ..., 400)

      # 1. ValidaÃ§Ã£o modo por_pessoa
      se data.modo_divisao == "por_pessoa":
          pessoas = json.loads(comanda.pessoas or "[]")
          se len(pessoas) < 2: raise AppError(PESSOAS_INSUFICIENTES, ..., 400)

      # 2. Calcular subtotal (excluir cancelados; cortesia tem preco_unitario=0 â†’ nÃ£o some)
      itens = get_itens_para_fechar(db, comanda_id)  # todos nÃ£o cancelados
      subtotal = sum(item.preco_unitario * item.quantidade for item in itens)

      total_pago = sum(p.valor for p in data.pagamentos)
      pagamento_parcial = (data.modo_divisao == "parcial")

      # 3. Calcular total com desconto (sÃ³ para fechamento total)
      if not pagamento_parcial:
          # Ler desconto armazenado na comanda
          if comanda.desconto_percentual:
              total_com_desconto = subtotal * (1 - comanda.desconto_percentual / 100)
          elif comanda.desconto_valor:
              total_com_desconto = subtotal - comanda.desconto_valor
          else:
              total_com_desconto = subtotal

          # Se hÃ¡ saldo_pendente (pagamento parcial anterior), usar saldo como base
          base = comanda.saldo_pendente if comanda.saldo_pendente else total_com_desconto

          se abs(total_pago - base) > Decimal("0.01"):
              raise AppError(PAGAMENTO_NAO_BATE, ..., 400)
      else:
          # Parcial: base = subtotal SEM desconto
          base = comanda.saldo_pendente if comanda.saldo_pendente else subtotal
          se total_pago >= base:
              raise AppError(PAGAMENTO_NAO_BATE, "Pagamento parcial deve ser menor que o total", ..., 400)

      # 4. Registrar pagamentos (dentro da transaÃ§Ã£o â€” usar flush)
      for p in data.pagamentos:
          metodo = db.get(MetodoPagamento, p.metodo_id)
          se nÃ£o existe: raise AppError(NOT_FOUND, ..., 404)
          create_pagamento(db, comanda_id, p.metodo_id, p.valor)

      itens_negativos = []

      if pagamento_parcial:
          novo_saldo = base - total_pago
          atualizar_saldo_pendente(db, comanda_id, novo_saldo)
      else:
          # 5. Baixar estoque e coletar insumos negativos
          for item in itens:
              negativos = _dar_baixa_estoque(db, item.item_id, item.quantidade)
              itens_negativos.extend(negativos)
          # 6. Fechar comanda
          fechar_comanda_repo(db, comanda_id, total_com_desconto)

      db.commit()
      db.refresh(comanda)
      response = _build_response(db, comanda)
      response.itens_negativos = itens_negativos
      return response
  ```

- [x] **E3.** `services/comandas_service.py` â€” adicionar `_dar_baixa_estoque`:
  ```python
  def _dar_baixa_estoque(db, item_id, quantidade) -> list[str]:
      """Baixa estoque; retorna nomes dos insumos que ficaram negativos."""
      item = db.get(Item, item_id)
      negativos = []
      if item.tipo == TipoItem.SIMPLES.value:
          negativos.extend(_baixar_insumo(db, item, quantidade))
      else:  # composto
          ficha = db.execute(select(FichaTecnica).where(FichaTecnica.item_id == item_id)).scalar_one_or_none()
          if ficha:
              componentes = db.execute(
                  select(ComponenteFicha).where(ComponenteFicha.ficha_id == ficha.id)
              ).scalars().all()
              for comp in componentes:
                  insumo = db.get(Item, comp.insumo_id)
                  negativos.extend(_baixar_insumo(db, insumo, comp.quantidade * quantidade))
      return negativos

  def _baixar_insumo(db, item, quantidade) -> list[str]:
      novo_estoque = item.estoque_atual - quantidade
      item.estoque_atual = novo_estoque
      registrar_movimento(db, item.id, TipoMovimento.SAIDA_VENDA, quantidade,
                          item.custo_medio, novo_estoque)
      db.flush()
      return [item.nome] if novo_estoque < 0 else []
  ```

- [x] **E4.** `services/comandas_service.py` â€” atualizar `_build_response`:
  ```python
  # Adicionar ao ComandaResponse:
  pagamentos_db = list_by_comanda(db, comanda.id)
  # Para cada pagamento, buscar MetodoPagamento para obter nome
  pagamentos = [PagamentoResponse(id=p.id, metodo_id=p.metodo_id,
                metodo_nome=db.get(MetodoPagamento, p.metodo_id).nome, valor=p.valor)
                for p in pagamentos_db]
  # + desconto_percentual, desconto_valor, total, saldo_pendente, data_fechamento
  # itens_negativos = [] (default â€” sÃ³ populado no fechar_comanda)
  ```

### Bloco F â€” Routes

- [x] **F1.** `api/routes/comandas.py` â€” adicionar 2 endpoints:
  ```python
  @router.post("/{comanda_id}/desconto", response_model=ComandaResponse)
  def aplicar_desconto(comanda_id: int, body: AplicarDescontoRequest,
                       db=Depends(get_db), _=Depends(get_current_user)):
      return comandas_service.aplicar_desconto(db, comanda_id, body)

  @router.post("/{comanda_id}/fechar", response_model=ComandaResponse)
  def fechar_comanda(comanda_id: int, body: FecharComandaRequest,
                     db=Depends(get_db), _=Depends(get_current_user)):
      return comandas_service.fechar_comanda(db, comanda_id, body)
  ```

### Bloco G â€” Tests

- [x] **G1.** `tests/test_fechamento.py` (10 testes):
  - `test_subtotal_exclui_cancelados` â€” item cancelado nÃ£o some no subtotal.
  - `test_cortesia_nao_some_subtotal_mas_baixa_estoque` â€” cortesia: subtotal=0, mas movimento de saÃ­da_venda criado.
  - `test_fechar_com_desconto_percentual` â€” subtotal 100, desconto 10% â†’ total 90, pagamento 90 OK.
  - `test_fechar_com_desconto_valor` â€” subtotal 100, desconto 8,90 â†’ total 91,10.
  - `test_pagamento_nao_bate_retorna_400` â€” total 90, pagar 80 sem modo parcial â†’ 400 PAGAMENTO_NAO_BATE.
  - `test_fechar_parcial_mantem_aberta` â€” pagar 50 de 90, comanda permanece `aberta`, saldo_pendente=40.
  - `test_fechar_parcial_calculado_sem_desconto` â€” subtotal 100, desconto 10%, parcial 50 â†’ vÃ¡lido (base=100 sem desconto).
  - `test_divisao_por_pessoa_sem_pessoas_retorna_400` â€” comanda sem pessoas, modo por_pessoa â†’ 400 PESSOAS_INSUFICIENTES.
  - `test_baixa_estoque_item_simples` â€” fechar comanda com item simples â†’ MovimentoEstoque criado, estoque_atual reduzido.
  - `test_baixa_estoque_composto_explode_ficha` â€” item composto com 2 insumos â†’ 2 movimentos criados, quantidades corretas.
  - `test_atomicidade_falha_nao_persiste` â€” forÃ§ar erro apÃ³s pagamentos mas antes do fechar â†’ status ainda 'aberta', sem pagamentos no banco.

### Bloco H â€” Frontend: Rota + App.tsx

- [x] **H1.** `App.tsx` â€” adicionar:
  ```tsx
  <Route path="/comandas/:id/fechar" element={<FechamentoPage />} />
  ```

### Bloco I â€” Frontend: Feature Fechamento

- [x] **I1.** `fechamentoSchemas.ts`:
  ```ts
  aplicarDescontoSchema = z.object({
    tipo: z.enum(["percentual", "valor"]),
    valor: z.coerce.number().positive(),
  })
  pagamentoSchema = z.object({
    metodo_id: z.number().int().positive(),
    valor: z.coerce.number().positive(),
  })
  fecharComandaSchema = z.object({
    pagamentos: z.array(pagamentoSchema).min(1),
    modo_divisao: z.enum(["sem_divisao", "igualmente", "por_pessoa", "parcial"]),
  })
  ```

- [x] **I2.** `useFechamento.ts`:
  - `useAplicarDesconto(comanda_id)` â€” mutation; POST /api/comandas/:id/desconto;
    onSuccess: invalidate `["comandas", comanda_id]`.
  - `useFecharComanda(comanda_id)` â€” mutation; POST /api/comandas/:id/fechar;
    onSuccess: toast verde "Comanda fechada com sucesso" + navigate `/comandas` (comprovante no Issue 8);
    onError 400 PAGAMENTO_NAO_BATE: toast vermelho persistente "Soma dos pagamentos nÃ£o confere com o total";
    onError 400 PESSOAS_INSUFICIENTES: toast vermelho "Cadastre ao menos 2 pessoas na comanda".
  - `useMetodosPagamento()` â€” useQuery `["metodos_pagamento"]`; GET /api/metodos-pagamento.

- [x] **I3.** `AplicarDescontoModal.tsx`:
  - Radio: Percentual (%) | Valor fixo (R$).
  - Input numÃ©rico com label dinÃ¢mico.
  - Submit â†’ `useAplicarDesconto`.
  - Exibir desconto atual se jÃ¡ aplicado (prefill).

- [x] **I4.** `FechamentoPage.tsx` (tela completa):
  - **Header:** `FECHAR COMANDA #ID â€” IDENTIFICAÃ‡ÃƒO`.
  - **Resumo:** lista de itens nÃ£o cancelados (nome, pessoa, subtotal), subtotal, desconto, total.
    - BotÃ£o "Aplicar/Editar Desconto" â†’ abre `AplicarDescontoModal`.
  - **Como dividir?** (RadioGroup 4 opÃ§Ãµes):
    - Sem divisÃ£o â€” formulÃ¡rio de pagamento livre.
    - Dividir igualmente â€” input "N pessoas", mostra valor por pessoa, preenche 1 pagamento automaticamente.
    - Cada pessoa paga valor diferente â€” lista com input por pessoa (soma deve bater com total), bloqueado < 2 pessoas.
    - Pagamento parcial â€” input "Quanto pagar agora?".
  - **Pagamento misto** (para modos sem_divisao e igualmente):
    - Lista de linhas: [Select mÃ©todo â–¼] [Input valor] [âœ• remover].
    - BotÃ£o "+ Adicionar mÃ©todo".
    - RodapÃ©: "Total recebido: R$ X" + indicador âœ“ se bate com total.
  - **BotÃ£o `[CONFIRMAR FECHAMENTO]`:**
    - Desabilitado se total recebido â‰  total (exceto modo parcial).
    - Modal de confirmaÃ§Ã£o antes de executar.
    - Chama `useFecharComanda`.
  - Loading skeleton enquanto carrega useComanda(id).
  - Toast amarelo se `itens_negativos.length > 0` pÃ³s-fechamento: "AtenÃ§Ã£o: estoque negativo em: [lista de nomes]".

- [x] **I5.** `ComandaAbertaPage.tsx` â€” adicionar botÃ£o:
  ```tsx
  <Button onClick={() => navigate(`/comandas/${id}/fechar`)}>
    [FECHAR CONTA]
  </Button>
  ```
  - Posicionado no rodapÃ© do painel direito (itens lanÃ§ados).

---

## ValidaÃ§Ãµes

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

## CritÃ©rios de Aceite (do Issue #7)

- [x] Schema `pagamentos` criado com FK para `comandas` e `metodos_pagamento`.
- [x] Colunas `desconto_percentual`, `desconto_valor`, `total`, `saldo_pendente`, `data_fechamento` em `comandas`.
- [x] `POST /api/comandas/{id}/desconto` aplica e persiste desconto na comanda aberta.
- [x] `POST /api/comandas/{id}/fechar` valida soma = total Â±0,01 (PAGAMENTO_NAO_BATE se errado).
- [x] Subtotal ignora itens cancelados e cortesias (preco_unitario=0 â†’ subtotal=0).
- [x] Desconto aplicado ao subtotal antes de validar pagamentos.
- [x] Pagamento parcial (modo="parcial"): comanda permanece `aberta`, saldo_pendente atualizado; base = subtotal SEM desconto.
- [x] Modo "por_pessoa" com < 2 pessoas â†’ 400 PESSOAS_INSUFICIENTES.
- [x] Fechamento total atÃ´mico: pagamentos + status fechada + baixa de estoque num Ãºnico `db.commit()`.
- [x] Baixa de estoque: itens simples â†’ 1 movimento; compostos â†’ explode ficha (1 movimento por insumo).
- [x] Cortesia: baixa de estoque executada (CMV registrado), mas nÃ£o some em subtotal/total.
- [x] Itens cancelados com `estornado=True` pulados na baixa de estoque.
- [x] Saldo negativo de estoque permitido; `itens_negativos` lista nomes no response.
- [x] FE: modal Aplicar Desconto funcional, tela Fechamento com 4 modos, toast amarelo em saldo negativo.
- [x] Testes: subtotal, desconto, pagamento, parcial, divisÃ£o, ficha composto, atomicidade, cortesia CMV.

---

## Notas Importantes

- **Atomicidade**: tudo em um Ãºnico `db.commit()` no final. Usar `db.flush()` apÃ³s cada registro intermediÃ¡rio (sem commit parcial).
- **Cortesia no CMV**: itens com `cortesia=True` sÃ£o incluÃ­dos na baixa de estoque (`get_itens_para_fechar` retorna todos nÃ£o-cancelados). O custo do insumo Ã© registrado no `movimentos_estoque` mesmo com subtotal=0.
- **Estornado=True pula baixa**: no loop de baixa, checar `item.estornado` â€” se True, pular (item foi cancelado com estorno, sem baixa no fechamento).
- **saldo_pendente**: quando hÃ¡ pagamento parcial anterior (saldo_pendente > 0), usar `saldo_pendente` como base ao invÃ©s de recalcular subtotal. Permite mÃºltiplos pagamentos parciais.
- **Python 3.9**: `Optional[X]` nÃ£o `X | None`, `list[X]` nÃ£o `List[X]`.
- **FichaTecnica â†’ ComponenteFicha**: usar `select(FichaTecnica).where(item_id=...)` e `select(ComponenteFicha).where(ficha_id=...)` â€” imports de `src.models.fichas_tecnicas` e `src.models.componentes_ficha`.
- **Imports no service**: `estoque_repository.registrar_movimento` e `estoque_repository.get_item_for_update` jÃ¡ existem â€” reusar.
- **`_build_response` com itens_negativos**: `itens_negativos` nÃ£o Ã© coluna no banco â€” Ã© calculado em tempo real no `fechar_comanda`. O `ComandaResponse` tem `itens_negativos: list[str] = []` como campo com default vazio (nÃ£o persistido).
- **ValidaÃ§Ã£o AplicarDescontoRequest**: exatamente um de `desconto_percentual` ou `desconto_valor` deve ser informado. Usar `@model_validator(mode="after")` do Pydantic v2.
- **Remover desconto**: para remover desconto aplicado, enviar `desconto_percentual=None` e `desconto_valor=None` (ambos None â†’ zera desconto). Ajustar validator.

---

## Tabela de DecisÃµes

| DecisÃ£o | Valor | Motivo |
|---|---|---|
| Modo divisÃ£o no backend | Apenas para validaÃ§Ã£o PESSOAS_INSUFICIENTES | FE calcula divisÃ£o; BE valida pagamentos |
| Cortesia na baixa | Sim (inclui) | CMV deve registrar custo mesmo sem receita |
| Estornado na baixa | Pular | Item jÃ¡ tratado no cancelamento manual |
| saldo_pendente como base | Sim, se > 0 | Evita recalcular subtotal em pagamentos sequenciais |
| itens_negativos no response | Calculado, nÃ£o persistido | InformaÃ§Ã£o transiente para toast do FE |
| Desconto em endpoint separado | Sim (/desconto antes de /fechar) | Permite revisar antes de confirmar |
| Fechar paga com saldo_pendente | saldo_pendente como base | Evitar recalcular quando hÃ¡ parcial anterior |

---

## PrÃ³ximos Passos PÃ³s-ConclusÃ£o

Issue #8 (Comprovante) consome:
- `GET /api/comandas/{id}` â†’ `ComandaResponse` com `pagamentos` e `total`.
- `desconto_percentual` / `desconto_valor` para exibir no comprovante.
- `data_fechamento` para timestamp do comprovante.

