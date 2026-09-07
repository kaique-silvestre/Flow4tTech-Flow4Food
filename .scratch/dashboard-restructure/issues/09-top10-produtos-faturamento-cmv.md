# 09: Top 10 Produtos — ordenar por faturamento + exibir CMV%

**What to build:** O widget "Top 10 Produtos" (último da lista, item 16 de 16) passa a ordenar por `faturamento` (em vez de quantidade) e mostrar `cmv_percentual`/`classificacao_cmv` de cada produto (tooltip ou label secundário ao lado da barra).

**Blocked by:** 02 (campos `cmv_percentual`/`classificacao_cmv` em `ProdutoTop` no backend)

**Touches:** `frontend/src/features/dashboard/DashboardPage.tsx` (ou subcomponente do gráfico Top 10, se existir separado)

**Nature:** objective

**Status:** ready-for-agent

- [ ] Gráfico/lista de Top 10 Produtos ordenado por `faturamento` descendente (era por quantidade)
- [ ] CMV% de cada produto exibido (tooltip ao passar o mouse na barra, ou label secundário ao lado) — usar `cmv_percentual`/`classificacao_cmv` vindos do backend
- [ ] Produto sem ficha técnica (`classificacao_cmv === "sem_custo"`, `cmv_percentual === null`) exibe algo como "sem custo cadastrado" em vez de "0%" ou "NaN%"
- [ ] Nenhuma regressão no restante do gráfico (cores, eixo, interatividade existente)
- [ ] Não é necessário usar `DashboardCard` aqui se o widget já tiver seu próprio wrapper visual consistente — mas se fizer sentido migrar para `DashboardCard` (ganhando "?" e skeleton padronizados), fazer também, já que este é o último item do lote de widgets do dashboard
