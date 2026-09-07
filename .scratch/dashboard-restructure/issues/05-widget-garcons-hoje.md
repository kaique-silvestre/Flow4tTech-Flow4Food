# 05: Widget "Garçons Hoje" (top 3)

**What to build:** Novo card no Dashboard usando `DashboardCard`, lista simples com nome + faturamento dos top 3 garçons do dia, usando `top_garcons_hoje`.

**Blocked by:** 02 (campo `top_garcons_hoje` no backend), 03 (`DashboardCard`)

**Touches:** `frontend/src/features/dashboard/DashboardPage.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [ ] Card "Garçons Hoje" posicionado após "Formas de Pagamento Hoje" e antes de "Comissões a Pagar" (ordem da spec: item 8 de 16)
- [ ] Usa `DashboardCard` (título, "?", skeleton)
- [ ] `helpText`: explica que mostra os 3 garçons com maior faturamento hoje
- [ ] Lista simples: nome + faturamento, top 3 de `top_garcons_hoje` (já vem truncado/ordenado do backend, mas não assumir — renderizar o que vier, no máximo 3)
- [ ] Loading state usa skeleton do `DashboardCard`
- [ ] Lista vazia (nenhuma venda hoje) mostra estado vazio razoável, sem quebrar
