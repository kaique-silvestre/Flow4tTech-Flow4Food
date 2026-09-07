# 02: Backend — novos campos em DashboardResponse + testes

**What to build:** Estender `dashboard_service.dashboard()` e `dashboard_schemas.DashboardResponse` com os 6 campos novos abaixo, todos com default seguro (não quebra consumidores atuais), reusando lógica existente em `relatorio_service`/`estoque_service` em vez de duplicar queries. Ler a spec completa `.scratch/dashboard-restructure/spec.md`, seções "Implementation Decisions > Backend" e "Testing Decisions", antes de implementar — as decisões de design já foram tomadas num grill e não devem ser reabertas.

**Blocked by:** None (can start immediately) — é o ticket fundacional que todos os widgets do front (03-08) dependem.

**Touches:** `backend/src/services/dashboard_service.py`, `backend/src/schemas/dashboard_schemas.py` (ou onde `DashboardResponse` estiver), `backend/tests/test_dashboard.py`, possivelmente `backend/src/services/estoque_service.py` (suporte a ordenação por `estoque_disponivel asc` em `get_saldo_list`)

**Nature:** objective

**Status:** ready-for-agent

- [ ] `por_metodo_pagamento_hoje: list[PagamentoResumo] = []` — NOVA query agregando `Pagamento` por `metodo_id` filtrando `Pagamento.created_at` dentro do dia corrente (mesmo padrão de `_day_utc_range` usado no resto do arquivo), independente do status da comanda. **Não** reusar a query de `fechamento_caixa`/`_build_por_metodo` (essa exclui pagamento parcial em comanda ainda aberta)
- [ ] Teste cobrindo o caso crítico: comanda com pagamento parcial hoje que **não** fechou (status aberto/reaberto) — o pagamento deve aparecer no total por método mesmo assim
- [ ] `top_garcons_hoje: list[VendasGarcomItem] = []` — reusa `vendas_por_garcom(db, hoje, hoje)` truncado para top 3 por faturamento, sem schema novo
- [ ] `perdas_cortesias_mes_total: Decimal = Decimal("0")` e `perdas_cortesias_mes_por_motivo: list[MotivoPerdaResumo] = []` (schema novo: `motivo`, `valor`) do mês corrente, reusando `perdas_cortesias`
- [ ] `comissoes_a_pagar_total: Decimal = Decimal("0")` e `comissoes_a_pagar_por_garcom: list[ComissaoGarcomResumo] = []` (schema novo: `garcom_id`, `nome`, `valor_pendente`) — soma de comissões com `pago=False`, sem filtro de data
- [ ] `insumos_menor_estoque: list[SaldoItemResponse] = []` — exatamente 5 insumos ordenados por `estoque_disponivel` ascendente via `estoque_service.get_saldo_list` (adicionar suporte a essa ordenação se não existir), **excluindo insumos já presentes em `insumos_criticos`**, sem classificação "baixo"/"alto"
- [ ] `top_10_produtos` reordenado por `faturamento` (em vez de quantidade); schema `ProdutoTop` ganha `cmv_percentual: Optional[float]` e `classificacao_cmv: str`, reusando a lógica de `cmv_por_produto` incluindo tratamento de produto sem ficha técnica (`classificacao="sem_custo"`, `cmv_percentual=None`)
- [ ] Testes em `backend/tests/test_dashboard.py` cobrindo cada campo novo com fixtures reais, seguindo o padrão de `backend/tests/test_relatorios_financeiros.py` (`test_cmv_classificacao_faixas`, `test_perdas_agrupadas_por_motivo`) e `backend/tests/test_estoque.py` — reutilizar fixtures (`_criar_produtos_com_ficha`, `_set_custo_medio`) em vez de recriar
- [ ] Teste garantindo que insumo crítico não aparece duplicado em `insumos_menor_estoque`
- [ ] Nenhum endpoint novo — tudo dentro do payload existente de `GET /dashboard`
- [ ] RLS por tenant automático via `tenant_id` nas novas queries, igual ao resto do arquivo — sem tratamento especial
