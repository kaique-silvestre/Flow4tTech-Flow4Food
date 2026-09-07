# 01: Breadcrumb genérico — toda tela mostra seu próprio label

**What to build:** `buildCrumbs` em `Breadcrumb.tsx` para de retornar `[]` para um item direto de `NAV_ITEMS` na sua rota raiz. Passa a retornar `[{label: item.label}]` — exceto para Dashboard (rota `/`, home, sem breadcrumb). Isso corrige Cardápio (hoje sem nenhum breadcrumb em `/cardapio`) e qualquer futuro item direto sem grupo.

**Blocked by:** None (can start immediately) — fundacional, baixo risco, mexe só em `Breadcrumb.tsx`.

**Touches:** `frontend/src/components/layout/Breadcrumb.tsx`, `frontend/src/components/layout/Breadcrumb.test.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [ ] `buildCrumbs("/cardapio")` retorna `[{label: "Cardápio"}]` (hoje retorna `[]`)
- [ ] `buildCrumbs("/")` continua retornando `[]` (Dashboard/home sem breadcrumb — não regride)
- [ ] `buildCrumbs("/cardapio/123", "Água Com Gás 500ml")` continua retornando `[{label: "Cardápio", to: "/cardapio"}, {label: "Água Com Gás 500ml"}]` — mecanismo dinâmico já existente não regride
- [ ] `buildCrumbs("/cardapio/123")` (sem label ainda carregado) continua retornando `[{label: "Cardápio"}]`, sem placeholder — comportamento já existente não regride
- [ ] Itens de grupo com `children` (Cadastros > Insumos, Estoque > Movimentos) continuam funcionando exatamente como hoje — não regride
- [ ] Item raiz do grupo sem sub-rota mais profunda (ex. clicar em "Compras" que é grupo redundante `item.label === child.label`) continua com o comportamento de colapso já existente ("Compras" sozinho, não "Compras > Compras")
- [ ] Teste em `Breadcrumb.test.tsx` cobrindo o novo caso (item direto na raiz mostra seu próprio label) além dos casos já existentes
