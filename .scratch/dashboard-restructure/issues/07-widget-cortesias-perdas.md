# 07: Widget "Cortesias/Perdas do Mês"

**What to build:** Novo card no Dashboard usando `DashboardCard`, valor total + breakdown por motivo (lista pequena, só se houver mais de um motivo), usando `perdas_cortesias_mes_total`/`_por_motivo`.

**Blocked by:** 02 (campos `perdas_cortesias_mes_total`/`_por_motivo` no backend), 03 (`DashboardCard`)

**Touches:** `frontend/src/features/dashboard/DashboardPage.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [ ] Card "Cortesias/Perdas do Mês" posicionado após "Comissões a Pagar" e antes de "Estoque — Atenção" (ordem da spec: item 10 de 16)
- [ ] Usa `DashboardCard` (título, "?", skeleton)
- [ ] `helpText`: explica que é o total de cortesias/perdas do mês corrente, para identificar vazamento de margem
- [ ] Valor total (`perdas_cortesias_mes_total`) em destaque
- [ ] Breakdown por motivo (`perdas_cortesias_mes_por_motivo`) exibido quando houver mais de um motivo com valor > 0 — não exibir lista de breakdown redundante se só há um motivo
- [ ] Loading state usa skeleton do `DashboardCard`
- [ ] Total zerado (sem cortesias/perdas no mês) mostra estado vazio razoável, sem quebrar
