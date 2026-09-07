# 05: Filtro de categoria via popover com árvore expansível

**What to build:** O `<select>` flat de categoria no Cardápio vira um popover ancorado no botão trigger (nasce/fecha na posição do botão, não no centro da tela), mostrando categoria-pai e subcategorias com hierarquia clara por indentação + peso de fonte — categoria-pai expansível, revelando subcategorias só quando expandida.

**Blocked by:** None (can start immediately)

**Touches:** novo componente em `frontend/src/features/cardapio/` (ex. `CategoriaFilterPopover.tsx`), `frontend/src/features/cardapio/CardapioPage.tsx`

**Nature:** mixed

**Status:** ready-for-agent

- [x] Popover baseado em Radix Popover (já instalado no projeto — `components/ui/popover.tsx`), ancorado no botão trigger
- [x] Reusa `useCategorias`/`Categoria[]` e a lógica de coleta de IDs por categoria-pai já existente (`collectIds` em `CardapioPage.tsx`)
- [x] Categoria-pai com estado expandido/colapsado (`Set<number>`); subcategoria só renderiza quando o pai está expandido
- [x] Categoria-pai em `font-medium`, subcategoria com peso/cor mais claros — hierarquia por indentação + tipografia, não por cor decorativa
- [x] Selecionar uma categoria-pai continua incluindo todas as suas subcategorias no filtro (comportamento de `collectIds` preservado)
- [x] Seleção é única (uma categoria/subcategoria por vez) — sem multi-seleção
- [x] Estado de expansão persiste em `useState` no componente pai enquanto a página está montada (expandir, fechar o popover, reabrir — continua expandido); não precisa sobreviver a reload de página
- [x] Filtro de categoria continua funcionando junto com busca por nome e filtro de status
- [x] Popover respeita `prefers-reduced-motion` (sem transição de entrada/saída elaborada quando ativo)
