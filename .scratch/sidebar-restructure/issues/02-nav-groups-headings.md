# 02: Nav agrupada com headings (Operação/Gestão)

**What to build:** O menu lateral passa a mostrar Dashboard e Calendário soltos no topo (sem heading), depois uma seção "OPERAÇÃO" (Cardápio, Vendas, Compras, Estoque) e uma seção "GESTÃO" (Financeiro, Relatórios, Cadastros), cada uma com um heading visual. Comportamento de clique/navegação dos itens continua idêntico ao de hoje — essa ticket só reorganiza a estrutura de dados e o agrupamento visual.

**Blocked by:** None (can start immediately)

**Touches:** `frontend/src/components/layout/navConfig.ts`, `frontend/src/components/layout/Sidebar.tsx`

**Nature:** mixed

- [ ] `navConfig.ts` expõe os itens organizados em grupos com heading opcional (estrutura de dado, não só JSX) — sem heading: Dashboard, Calendário; "OPERAÇÃO": Cardápio, Vendas, Compras, Estoque; "GESTÃO": Financeiro, Relatórios, Cadastros. "Configurações" segue no dado por ora (sai da lista principal só na ticket 06).
- [ ] `Sidebar.tsx` renderiza os headings de seção (label uppercase, estilo discreto) acima de cada grupo.
- [ ] Filtragem por permissão/feature flag (`usePermissions`, `useFeatureFlags`) continua funcionando igual — grupo sem nenhum item visível não aparece, heading de grupo vazio também não aparece.
- [ ] Nenhuma mudança de comportamento de clique/rota nos itens existentes.
