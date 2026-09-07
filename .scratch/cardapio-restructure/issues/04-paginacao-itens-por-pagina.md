# 04: Paginação com seletor de itens por página

**What to build:** `components/ui/pagination.tsx` ganha um seletor de itens por página (10/25/50), e o Cardápio usa esse seletor em vez do tamanho fixo de 10 atual.

**Blocked by:** None (can start immediately)

**Touches:** `components/ui/pagination.tsx`, `frontend/src/features/cardapio/CardapioPage.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [x] `Pagination` aceita nova prop `porPagina` + `onPorPaginaChange`, controlada pelo componente pai
- [x] Seletor nativo (`<select>`) com opções 10/25/50
- [x] Valor padrão ao abrir a tela: 10 (comportamento atual preservado pra quem nunca mexeu)
- [x] Trocar o valor recalcula a paginação e volta pra página 1
- [x] Escolha NÃO persiste entre visitas (sem `localStorage`) — volta a 10 toda vez que a tela é reaberta
- [x] Sem dependência nova instalada (sem MUI DataGrid)
