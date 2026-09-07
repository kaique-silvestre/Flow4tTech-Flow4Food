# 05: Busca/filtro local dos itens do menu

**What to build:** Usuário digita num campo de busca na sidebar e vê só os itens (ou grupos cujo filho bate) que correspondem ao texto — filtro 100% client-side, instantâneo, sem chamada de rede.

**Blocked by:** 02

**Touches:** `frontend/src/components/layout/navConfig.ts`, `frontend/src/components/layout/Sidebar.tsx`

**Nature:** mixed

- [ ] Função pura `filterNavItems(query, groups)` exportada de `navConfig.ts` (ou módulo irmão): retorna os grupos/itens que batem por `label`, case-insensitive; string vazia retorna tudo sem filtrar; item pai aparece se ele mesmo bate OU se algum filho bate (nesse caso, mostra só os filhos que batem).
- [ ] Campo de busca renderizado na sidebar, abaixo do bloco Empresa (ticket 03) e acima da lista de grupos.
- [ ] Digitar filtra a lista em tempo real, sem debounce (lista já está em memória).
- [ ] Testes unitários (Vitest puro, sem DOM) para `filterNavItems`: item de topo batendo, filho batendo (mostra só o filho que bate), busca vazia retorna tudo, busca sem match nenhum retorna lista vazia.
