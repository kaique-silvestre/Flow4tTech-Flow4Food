# PRP — Issue #9: Reabertura de comanda + estorno de estoque

**Parent PRD:** `docs/prd_matchpoint_mvp.md`
**Parent Issue:** `docs/issues_matchpoint_mvp.md` → Issue 9
**Documento mestre:** `docs/matchpoint_documentacao.md` §9.4
**Type:** AFK
**Status:** Concluída ✓ (2026-05-07)
**Criado em:** 2026-05-07
**Depende de:** Issue #7 (Fechamento) — concluída

---

## Objetivo

Reabertura de comanda fechada com estorno atômico de estoque (§9.4). Inclui:
- `POST /api/comandas/{id}/reabrir` — só aceita `status == fechada`; código `COMANDA_NAO_FECHADA` caso contrário.
- Transação atômica: estorna estoque dos itens não-cancelados (explode ficha em compostos), muda status para `reaberta`, registra evento `comanda_reaberta`.
- `GET /api/comandas/fechadas` — lista comandas fechadas para histórico no FE.
- `list_abertas` passa a incluir também `reaberta` (comanda volta ao fluxo normal).
- FE: seção "Histórico" em `ComandasPage` com comandas fechadas.
- FE: botão `[REABRIR COMANDA]` em `ComandaAbertaPage` quando `status === "fechada"`, com modal de confirmação.
- Após reabertura: comanda aparece na lista principal (abertas+reaberta), pode ser fechada novamente.

---

## Estrutura de Arquivos a Criar/Modificar

```
backend/
  src/
    models/
      comandas.py                           # (modificar) StatusComanda: + REABERTA
      eventos_comanda.py                    # (modificar) TipoEvento: + COMANDA_REABERTA
      movimentos_estoque.py                 # (modificar) TipoMovimento: + ENTRADA_ESTORNO

    core/
      errors.py                             # (modificar) ErrorCode: + COMANDA_NAO_FECHADA

    repositories/
      comandas_repository.py               # (modificar) reabrir_comanda_repo, list_fechadas,
                                            # list_abertas inclui REABERTA

    services/
      comandas_service.py                  # (modificar) reabrir_comanda, _estornar_estoque

    api/
      routes/
        comandas.py                        # (modificar) POST /{id}/reabrir, GET /fechadas

  tests/
    test_reabertura.py                     # 6 testes

frontend/
  src/
    features/
      comandas/
        useComandas.ts                     # (modificar) useComandasFechadas, useReopenComanda
        ComandasPage.tsx                   # (modificar) seção Histórico com fechadas
        ComandaAbertaPage.tsx              # (modificar) botão Reabrir + modal confirmação
```

**Sem migration** — não há novas tabelas ou colunas. Todos os valores novos são strings em colunas `VARCHAR` existentes.

---

## Tarefas

### Bloco A — Models (enums)

- [x] **A1.** `models/comandas.py` — adicionar ao `StatusComanda`:
  ```python
  REABERTA = "reaberta"
  ```

- [x] **A2.** `models/eventos_comanda.py` — adicionar ao `TipoEvento`:
  ```python
  COMANDA_REABERTA = "comanda_reaberta"
  ```

- [x] **A3.** `models/movimentos_estoque.py` — adicionar ao `TipoMovimento`:
  ```python
  ENTRADA_ESTORNO = "entrada_estorno"
  ```

### Bloco B — ErrorCode

- [x] **B1.** `core/errors.py` — adicionar ao `ErrorCode`:
  ```python
  COMANDA_NAO_FECHADA = "COMANDA_NAO_FECHADA"
  ```

### Bloco C — Repository

- [x] **C1.** `repositories/comandas_repository.py` — modificar `list_abertas` para incluir `REABERTA`:
  ```python
  def list_abertas(db: Session, busca: Optional[str] = None) -> list[Comanda]:
      q = db.query(Comanda).filter(
          Comanda.status.in_([StatusComanda.ABERTA.value, StatusComanda.REABERTA.value])
      )
      if busca:
          q = q.filter(Comanda.identificacao.ilike(f"%{busca}%"))
      return q.order_by(Comanda.created_at.desc()).all()
  ```

- [x] **C2.** `repositories/comandas_repository.py` — adicionar `list_fechadas`:
  ```python
  def list_fechadas(db: Session, busca: Optional[str] = None) -> list[Comanda]:
      q = db.query(Comanda).filter(Comanda.status == StatusComanda.FECHADA.value)
      if busca:
          q = q.filter(Comanda.identificacao.ilike(f"%{busca}%"))
      return q.order_by(Comanda.data_fechamento.desc()).all()
  ```

- [x] **C3.** `repositories/comandas_repository.py` — adicionar `reabrir_comanda_repo`:
  ```python
  def reabrir_comanda_repo(db: Session, comanda_id: int) -> None:
      comanda = db.query(Comanda).filter(Comanda.id == comanda_id).first()
      if comanda is not None:
          comanda.status = StatusComanda.REABERTA.value
          comanda.total = None
          comanda.data_fechamento = None
          comanda.saldo_pendente = None
      db.flush()
  ```

### Bloco D — Service

- [x] **D1.** `services/comandas_service.py` — adicionar `reabrir_comanda`:
  ```python
  def reabrir_comanda(db: Session, comanda_id: int) -> ComandaResponse:
      comanda = comandas_repository.get_by_id(db, comanda_id)
      if comanda is None:
          raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)
      if comanda.status != StatusComanda.FECHADA.value:
          raise AppError(ErrorCode.COMANDA_NAO_FECHADA,
                         "Apenas comandas fechadas podem ser reabertas", http_status=400)

      # Estornar estoque dos itens não-cancelados
      itens = comandas_repository.get_itens_para_fechar(db, comanda_id)
      for item in itens:
          _estornar_estoque(db, item.item_id, item.quantidade)

      # Mudar status e limpar campos de fechamento
      comandas_repository.reabrir_comanda_repo(db, comanda_id)

      # Registrar evento
      comandas_repository.add_evento(
          db, comanda_id, TipoEvento.COMANDA_REABERTA, {}, comanda.garcom_id
      )

      db.commit()
      db.refresh(comanda)
      return _build_response(db, comanda)
  ```

- [x] **D2.** `services/comandas_service.py` — adicionar `_estornar_estoque`:
  ```python
  def _estornar_estoque(db: Session, item_id: int, quantidade: Decimal) -> None:
      """Estorna estoque de item (simples direto; composto explode ficha)."""
      item = db.get(Item, item_id)
      if item is None:
          return
      if item.tipo == TipoItem.SIMPLES.value:
          _estornar_insumo(db, item, quantidade)
      else:
          ficha = db.execute(
              select(FichaTecnica).where(FichaTecnica.item_id == item_id)
          ).scalar_one_or_none()
          if ficha:
              componentes = db.execute(
                  select(ComponenteFicha).where(ComponenteFicha.ficha_id == ficha.id)
              ).scalars().all()
              for comp in componentes:
                  insumo = db.get(Item, comp.insumo_id)
                  if insumo is not None:
                      _estornar_insumo(db, insumo, comp.quantidade * quantidade)

  def _estornar_insumo(db: Session, item: Item, quantidade: Decimal) -> None:
      novo_estoque = item.estoque_atual + quantidade
      item.estoque_atual = novo_estoque
      estoque_repository.registrar_movimento(
          db, item.id, TipoMovimento.ENTRADA_ESTORNO, quantidade,
          item.custo_medio, novo_estoque
      )
      db.flush()
  ```

### Bloco E — Route

- [x] **E1.** `api/routes/comandas.py` — adicionar 2 endpoints:
  ```python
  @router.post("/{comanda_id}/reabrir", response_model=ComandaResponse)
  def reabrir_comanda(
      comanda_id: int,
      db: Session = Depends(get_db),
      _user: dict = Depends(get_current_user),
  ) -> ComandaResponse:
      return comandas_service.reabrir_comanda(db, comanda_id)

  @router.get("/fechadas", response_model=list[ComandaResponse])
  def list_fechadas(
      busca: Optional[str] = Query(None),
      db: Session = Depends(get_db),
      _user: dict = Depends(get_current_user),
  ) -> list[ComandaResponse]:
      from src.repositories import comandas_repository as cr
      from src.services.comandas_service import _build_response
      comandas = cr.list_fechadas(db, busca)
      return [_build_response(db, c) for c in comandas]
  ```
  **Atenção:** `GET /fechadas` deve ser registrado ANTES de `GET /{comanda_id}` no router para não colidir com o path param.

### Bloco F — Tests

- [x] **F1.** `tests/test_reabertura.py` (6 testes):
  - `test_reabrir_comanda_fechada_ok` — fecha comanda com item simples → reabre → status `reaberta`, estoque restaurado, evento registrado.
  - `test_reabrir_estorna_item_composto` — fecha com item composto (2 insumos) → reabre → 2 movimentos ENTRADA_ESTORNO, estoques corretos.
  - `test_reabrir_comanda_aberta_retorna_400` — comanda com status `aberta` → 400 `COMANDA_NAO_FECHADA`.
  - `test_reabrir_comanda_parcial_retorna_400` — comanda em pagamento parcial (status `aberta`) → 400 `COMANDA_NAO_FECHADA`.
  - `test_reabrir_comanda_inexistente_retorna_404` — id inválido → 404.
  - `test_reaberta_aparece_na_lista_abertas` — após reabertura, comanda aparece em `GET /api/comandas`.

### Bloco G — Frontend: useComandas

- [x] **G1.** `features/comandas/useComandas.ts` — adicionar:
  ```ts
  export function useComandasFechadas(busca?: string) {
    return useQuery<ComandaResponse[]>({
      queryKey: ["comandas", "fechadas", busca],
      queryFn: () =>
        api.get<ComandaResponse[]>("/api/comandas/fechadas", { params: { busca } })
          .then((r) => r.data),
    });
  }

  export function useReopenComanda(comanda_id: number | string) {
    const qc = useQueryClient();
    const navigate = useNavigate();
    return useMutation({
      mutationFn: () =>
        api.post<ComandaResponse>(`/api/comandas/${comanda_id}/reabrir`).then((r) => r.data),
      onSuccess: () => {
        qc.invalidateQueries({ queryKey: ["comandas"] });
        toast.success("Comanda reaberta com sucesso");
        navigate(`/comandas/${comanda_id}`);
      },
      onError: (err: unknown) => {
        const msg = (err as { response?: { data?: ApiErrorBody } })?.response?.data?.error?.message;
        toast.error(msg ?? "Erro ao reabrir comanda");
      },
    });
  }
  ```

### Bloco H — Frontend: ComandasPage

- [x] **H1.** `features/comandas/ComandasPage.tsx` — adicionar seção "Histórico":
  - Abaixo da lista de abertas, seção colapsável "Histórico (Fechadas)" com busca própria.
  - Usa `useComandasFechadas(buscaFechadas)`.
  - Card clicável → `navigate(\`/comandas/${c.id}\`)`.
  - Mostra: identificação, garçom, total, data_fechamento formatada.
  - Estado colapsado por default (`useState(false)`).

### Bloco I — Frontend: ComandaAbertaPage

- [x] **I1.** `features/comandas/ComandaAbertaPage.tsx` — adicionar Reabrir quando `comanda.status === "fechada"`:
  - Mostrar um painel simplificado (readonly) com lista de itens e resumo financeiro.
  - Botão `[REABRIR COMANDA]` no rodapé.
  - Botão `[VER COMPROVANTE]` → `navigate(\`/comprovante/${id}\`)`.
  - Ao clicar [REABRIR]: abrir modal de confirmação inline (estado `useState(false)`).
  - Modal: texto "Ao reabrir, o estoque será estornado e a comanda voltará ao fluxo de lançamento. Deseja continuar?" + botões [Cancelar] / [Confirmar Reabertura].
  - Confirmar → `useReopenComanda(comanda_id).mutate()`.
  - Quando `comanda.status === "reaberta"` ou `"aberta"`: renderiza o formulário de lançamento normal (comportamento atual).

---

## Validações

### Backend
```bash
ruff check .
mypy src/
pytest tests/ -v
```

### Frontend
```bash
npm run type-check
npm run lint
npm run build
```

---

## Critérios de Aceite

- [x] `StatusComanda.REABERTA = "reaberta"` adicionado.
- [x] `TipoEvento.COMANDA_REABERTA` adicionado.
- [x] `TipoMovimento.ENTRADA_ESTORNO` adicionado.
- [x] `ErrorCode.COMANDA_NAO_FECHADA` adicionado.
- [x] `POST /api/comandas/{id}/reabrir` só aceita `status=fechada`; 400 `COMANDA_NAO_FECHADA` caso contrário.
- [x] Transação atômica: estorno + status REABERTA + evento numa única `db.commit()`.
- [x] Item simples: 1 movimento `ENTRADA_ESTORNO`, estoque incrementado.
- [x] Item composto: 1 movimento por insumo da ficha técnica.
- [x] `list_abertas` retorna também `reaberta`.
- [x] `GET /api/comandas/fechadas` retorna lista de fechadas.
- [x] Testes: 6 cenários passando.
- [x] FE: seção Histórico em ComandasPage com fechadas.
- [x] FE: botão Reabrir em ComandaAbertaPage quando status=fechada, com modal de confirmação.
- [x] FE: após reabertura, navigate para `/comandas/:id` (volta ao fluxo normal).

---

## Notas Importantes

- **Sem migration** — `status`, `tipo` (eventos), `tipo` (movimentos) são todos colunas VARCHAR que aceitam qualquer string. Apenas adicionamos novos valores ao enum Python/TS.
- **GET /fechadas antes de GET /:id** — no FastAPI, rotas com path params genéricos devem vir depois de rotas estáticas. `GET /fechadas` precisa ser declarado antes de `GET /{comanda_id}` no mesmo router.
- **`reabrir_comanda_repo` zera `total`, `data_fechamento`, `saldo_pendente`** — limpa os campos preenchidos no fechamento para evitar confusão na reabertura.
- **`_estornar_estoque` não verifica `estornado`** — na reabertura, estornamos todos os não-cancelados. Itens cancelados com `estornado=True` não foram incluídos na baixa original (Issue 7) nem aqui.
- **`get_itens_para_fechar`** — já filtra apenas `cancelado=False`. Reutilizar para obter itens a estornar.
- **Python 3.9**: `Optional[X]` não `X | None`.
- **`TipoEvento` é usado como string**: `add_evento(db, comanda_id, TipoEvento.COMANDA_REABERTA, ...)`.
- **Desconto não é zerado** — na reabertura, manter `desconto_percentual` e `desconto_valor` (usuário pode querer fechar de novo com desconto).
- **Pagamentos não são deletados** — os pagamentos registrados no fechamento permanecem no banco; na reabertura a comanda fica com `total=None` mas os registros históricos de pagamento existem. Isso é aceitável para MVP (relatórios futuros usarão apenas comandas `fechadas`).
