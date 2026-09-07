# 06: Widget "Comissões a Pagar"

**What to build:** Novo card no Dashboard usando `DashboardCard`, valor total + breakdown por garçom direto no card, usando `comissoes_a_pagar_total`/`_por_garcom`. Clicável, navega para `/cadastros/garcons` como atalho complementar (não como única forma de ver detalhe — o breakdown já está no card).

**Blocked by:** 02 (campos `comissoes_a_pagar_total`/`_por_garcom` no backend), 03 (`DashboardCard`)

**Touches:** `frontend/src/features/dashboard/DashboardPage.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [ ] Card "Comissões a Pagar" posicionado após "Garçons Hoje" e antes de "Cortesias/Perdas do Mês" (ordem da spec: item 9 de 16)
- [ ] Usa `DashboardCard` (título, "?", skeleton)
- [ ] `helpText`: explica que é a soma de comissões pendentes de pagamento (não é um corte mensal, é dívida em aberto)
- [ ] Valor total (`comissoes_a_pagar_total`) em destaque
- [ ] Breakdown por garçom: lista curta nome + valor pendente, usando `comissoes_a_pagar_por_garcom`
- [ ] Card clicável → navega para `/cadastros/garcons` (mesmo padrão de navegação de "Comandas Abertas" existente no dashboard)
- [ ] Loading state usa skeleton do `DashboardCard`
- [ ] Total zerado (nenhuma comissão pendente) mostra estado vazio razoável, sem quebrar
