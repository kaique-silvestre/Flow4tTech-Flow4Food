# PRP — Issue #17: Engine de desconto no PDV
**GitHub Issue:** #17 | **Type:** AFK | **Depende de:** #14

## Tarefas

### Bloco A — Migration
- [ ] A1. Migration 0062: ADD COLUMN promocao_id BIGINT FK promocoes(id) SET NULL em itens_comanda

### Bloco B — Model + Repository
- [ ] B1. ItemComanda: adicionar campo promocao_id Optional FK
- [ ] B2. add_item em comandas_repository: adicionar parâmetro promocao_id=None

### Bloco C — Engine de desconto
- [ ] C1. Criar helper resolve_promo(db, produto_id) → Optional[Promocao]:
           1. Buscar promocoes ativas para produto_id via PromocaoProduto JOIN Promocao
           2. Filtro de vigência: data_inicio <= hoje <= data_fim (ou data_fim IS NULL)
           3. Filtro de horário: hora_inicio <= hora_atual <= hora_fim
           4. Filtro de recorrência:
              - nenhuma: sem filtro adicional
              - semanal: date.today().weekday() mapeado p/ 0=Dom…6=Sáb está em dias_semana
              - mensal: date.today().day está em dias_mes
           5. Conflito: retornar promoção com menor id
- [ ] C2. Criar helper apply_discount(preco_venda, promo) → Decimal:
           porcentagem: preco_venda * (1 - valor_desconto/100)
           valor_fixo: max(0, preco_venda - valor_desconto)
           Resultado arredondado para 2 casas

### Bloco D — Integração em lancar_item
- [ ] D1. Após calcular preco_unitario (linha 206), se not cortesia:
           promo = resolve_promo(db, produto.id)
           preco_unitario = apply_discount(preco_unitario, promo) if promo else preco_unitario
           promocao_id = promo.id if promo else None
- [ ] D2. Passar promocao_id para add_item
- [ ] D3. Incluir promocao_id no evento ITEM_LANCADO

### Bloco E — Schema
- [ ] E1. ItemComandaResponse: adicionar campos promocao_id Optional[int] + promocao_nome Optional[str]
- [ ] E2. _build_item_response em comandas_service: popular promocao_nome via query Promocao

### Bloco F — Testes (arquivo: tests/test_issue17_desconto_pdv.py)
- [ ] F1. Item com promo ativa (porcentagem) → preco_unitario descontado, promocao_id preenchido
- [ ] F2. Item com promo ativa (valor_fixo) → preco correto
- [ ] F3. Item fora da janela de horário → sem desconto
- [ ] F4. Item cortesia → sem desconto (preco=0)
- [ ] F5. Conflito: duas promos ativas → aplica menor id
- [ ] F6. Recorrência semanal: dia errado → sem desconto

## Validações
- `cd backend && python -m pytest`
