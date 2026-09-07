# 06: Página de produto (/cardapio/:id) + breadcrumb dinâmico

**What to build:** Clicar em qualquer parte da linha de um produto na lista do Cardápio navega para uma página dedicada (`/cardapio/:id`) mostrando nome, categoria, preço e ficha técnica em tabela editável (colunas Insumo | Quantidade | Unidade | Custo | remover), com Desativar/Reativar disponível ali também e um breadcrumb "Cardápio > Nome do Produto" que sabe voltar pra lista. O botão "Editar" e o chevron de expandir ficha técnica inline somem da lista (substituídos pela página). O mecanismo de breadcrumb dinâmico é genérico, reutilizável por qualquer futura rota `/x/:id`, não hardcoded pro Cardápio.

**Blocked by:** 01 (Componente Table + migrar tabela do Cardápio) — a página usa `components/ui/table.tsx` pra ficha técnica

**Touches:** `frontend/src/App.tsx`, `frontend/src/features/cardapio/ProdutoPage.tsx` (novo), `frontend/src/features/cardapio/ProdutoModal.tsx`, `frontend/src/features/cardapio/CardapioPage.tsx`, `frontend/src/components/layout/Breadcrumb.tsx`, `frontend/src/components/layout/AppLayout.tsx`

**Nature:** mixed

**Status:** ready-for-agent

- [x] Nova rota `/cardapio/:id` registrada em `App.tsx`, mesmo padrão de `/consumo-interno/:consumidorId`
- [x] `ProdutoPage.tsx` mostra nome, categoria, preço e ficha técnica (tabela com `components/ui/table.tsx`, colunas Insumo | Quantidade | Unidade | Custo | remover), reaproveitando `useProdutos`/`useCreateProduto`/`useUpdateProduto`
- [x] Clicar em qualquer parte da linha do produto na lista (exceto botões de ação) navega para `/cardapio/{id}`
- [x] Botões "Desativar"/"Reativar" na linha usam `stopPropagation` — não disparam a navegação
- [x] Botão "Editar" removido da lista (redundante com a linha clicável)
- [x] Chevron de expandir ficha técnica inline removido da lista (informação agora vive só na página)
- [x] Ação Desativar/Reativar também disponível na página do produto
- [x] `ProdutoModal.tsx` (criação rápida) continua existindo só pra criar; ao salvar com sucesso, navega para `/cardapio/{id}` do produto recém-criado em vez de só fechar o modal
- [x] Ficha técnica dentro do `ProdutoModal.tsx` também usa a tabela nova (consistência visual com a página)
- [x] `Breadcrumb.tsx`/`buildCrumbs`: item direto de `NAV_ITEMS` com rota mais profunda (`pathname.startsWith(item.to + "/")`) monta `[{label: item.label, to: item.to}, {label: <dinâmico>}]` em vez de retornar `[]` incondicionalmente
- [x] Mecanismo de label dinâmico é genérico: um contexto (`BreadcrumbContext`) provido em `AppLayout.tsx` + hook (`useBreadcrumbLabel`) que qualquer página de detalhe pode chamar — não um `if pathname.includes("cardapio")` hardcoded
- [x] `ProdutoPage.tsx` chama `useBreadcrumbLabel(produto?.nome)` quando os dados carregam, limpa ao desmontar
- [x] Enquanto o nome do produto ainda não carregou ou o produto não existe (404), o breadcrumb mostra só "Cardápio" (sem placeholder tipo "...", sem piscar)
- [x] Item raiz sem rota mais profunda (ex. `/cardapio` sozinho) continua sem breadcrumb, comportamento atual preservado
- [x] Grupo com `children` estático (ex. Estoque > Movimentos) continua funcionando como hoje, sem regressão
- [x] Navegação para a página de produto respeita `prefers-reduced-motion` (sem transição elaborada)
