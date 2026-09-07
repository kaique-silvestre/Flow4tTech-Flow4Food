# 02: Busca normalizada no Cardápio

**What to build:** A busca por nome de produto no Cardápio ignora acentuação e caixa — digitar "agua" encontra "Água Com Gás 500ml".

**Blocked by:** None (can start immediately)

**Touches:** `frontend/src/features/cardapio/CardapioPage.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [x] Normalizar via `.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()` tanto o termo de busca quanto `produto.nome` antes de comparar com `.includes()`
- [x] Buscar "agua" encontra "Água Com Gás 500ml" e "Água Sem Gás 500ml"
- [x] Buscar "AGUA" (caixa alta) encontra os mesmos resultados
- [x] Busca continua funcionando junto com o filtro de status (Ativos/Inativos/Todos) e o filtro de categoria — filtros combinados, não um substituindo o outro
- [x] Produtos inativos continuem aparecendo nos filtros "Inativos"/"Todos" com a busca aplicada
- [x] Sem biblioteca nova instalada
