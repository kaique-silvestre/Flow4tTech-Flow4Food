# 04: Widget "Formas de Pagamento Hoje"

**What to build:** Novo card no Dashboard usando `DashboardCard`, com donut chart (Recharts `PieChart`) mostrando `por_metodo_pagamento_hoje`.

**Blocked by:** 02 (campo `por_metodo_pagamento_hoje` no backend), 03 (`DashboardCard`)

**Touches:** `frontend/src/features/dashboard/DashboardPage.tsx`, possivelmente `frontend/src/features/dashboard/components/` (subcomponente do gráfico, se fizer sentido extrair)

**Nature:** objective

**Status:** ready-for-agent

- [ ] Card "Formas de Pagamento Hoje" posicionado após "Comandas (abertas/fechadas hoje)" e antes de "Garçons Hoje" (ordem da spec: item 7 de 16)
- [ ] Usa `DashboardCard` (título, "?", skeleton)
- [ ] `helpText`: explica que é a soma dos pagamentos recebidos hoje por forma de pagamento, incluindo pagamento parcial de comanda ainda aberta
- [ ] Donut chart (Recharts `PieChart`) com `por_metodo_pagamento_hoje`
- [ ] Loading state usa skeleton do `DashboardCard` (cross-fade ao carregar dados)
- [ ] Lista vazia (sem pagamentos hoje) não quebra o gráfico — mostra estado vazio razoável
- [ ] Nenhuma dependência nova (Recharts já usado em outros gráficos do dashboard — confirmar import correto)
