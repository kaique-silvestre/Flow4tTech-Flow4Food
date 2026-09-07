Status: ready-for-agent

# Reestruturação da aba Cardápio (Matchpoint)

## Problem Statement

A aba Cardápio (`/cardapio`) tem vários atritos que o dono do bar sente no dia a dia:

1. A busca de produto é sensível a acento e caixa — digitar "agua" não encontra "Água", o que faz parecer que o produto não existe.
2. O filtro de categoria é um `<select>` flat que só indenta visualmente subcategorias com espaços — em telas reais (32 produtos, categorias com 2 níveis: ex. `Bebidas > Cervejas`) fica difícil diferenciar rapidamente o que é categoria-pai do que é subcategoria.
3. O botão "A→Z" alterna a ordenação mas não deixa claro visualmente que é um toggle com dois estados (ordenado / ordem original) — parece quebrado.
4. A tabela de produtos é densamente visual (8 colunas, sem componente de tabela reutilizável, `<table>` cru estilizado inline) e os botões de ação (Editar/Desativar/Reativar) usam estilo datado.
5. O modal "Novo Produto"/"Editar Produto" é apertado: nome, categoria, preço e ficha técnica inteira (lista de insumos com selects soltos, sem cabeçalho de colunas) tudo dentro de um `Dialog` de largura fixa. Ficha técnica em particular não tem estrutura de tabela — vira uma pilha de linhas de controles sem rótulo.
6. Clicar em "Editar" é a única forma de ver o detalhe de um produto — não existe uma tela dedicada por produto, então não há espaço para crescer (histórico, mais contexto de ficha técnica) sem apertar ainda mais o modal.
7. Cardápio não tem breadcrumb (`Estoque` mostra "Estoque" abaixo do header; `/cardapio` não mostra nada) — causa raiz: `Cardápio` é um item de navegação direto sem `children` em `NAV_ITEMS`, e `Breadcrumb.tsx` pula (`buildCrumbs` retorna `[]`) qualquer item direto, mesmo quando a rota atual é mais profunda que o item (ex.: uma futura `/cardapio/:id`). `Estoque` só tem breadcrumb porque é um grupo com `children` estáticos (`Estoque`, `Movimentos`).
8. As tabelas de Cardápio e Estoque usam markup quase idêntico (`<table>` cru, mesmas classes `border-b`/`py-2`/`pr-4`) mas com convenções diferentes: Cardápio alinha todas as colunas numéricas à direita; Estoque só alinha a última coluna, deixando `Estoque atual`/`Reservado`/`Disponível`/`Custo médio` alinhados à esquerda. O resultado visual é duas tabelas parecidas mas não iguais.
9. `/estoque/movimentos` (`MovimentosPage.tsx`) tem duas tabelas raw `<table>` (aba "Insumos" e aba "Produtos") com o mesmo problema de alinhamento (`Quantidade`/`Preço unit.`/`Subtotal`/`Saldo após` alinhados à esquerda). Além disso, a aba ativa é `useState` local — trocar de aba não muda a URL, então não dá pra compartilhar link direto pra "Produtos" nem usar o botão voltar do navegador pra desfazer a troca.

## Solution

Reestruturar a aba Cardápio em cinco frentes, todas usando os termos do glossário do projeto (Insumo, Ficha Técnica, CMV — ver `CONTEXT.md`):

1. **Busca normalizada**: comparar busca e nome do produto ignorando acentuação e caixa (normalização via NFD + remoção de diacríticos + lowercase nos dois lados da comparação).
2. **Filtro de categoria via popover com árvore expansível**: substitui o `<select>` flat por um popover ancorado no botão trigger (nasce e fecha na posição do botão, não no centro da tela — consistência espacial), com categorias-pai expansíveis revelando subcategorias, hierarquia por indentação + peso de fonte (categoria-pai em `font-medium`, subcategoria mais clara), não por cor decorativa.
3. **Toggle de ordenação com estado explícito**: o controle A→Z passa a indicar visualmente qual dos dois estados está ativo (ordem alfabética vs. ordem de cadastro) sem depender só de contraste de fundo — rótulo ou ícone que muda conforme o estado.
4. **Novo componente de tabela reutilizável** (`components/ui/table.tsx`, estilo shadcn: `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell`) para substituir o `<table>` cru — adotado primeiro na tabela de produtos do Cardápio, disponível para as demais tabelas do sistema migrarem depois (fora de escopo migrar as outras agora). Mantém Tailwind + Radix (stack já usada no projeto, sem introduzir MUI/DataGrid — ver Implementation Decisions).
5. **Página dedicada por produto** (`/cardapio/:id`): clicar em qualquer parte da linha do produto (não um botão dedicado — ver precedente `PlatformTenantsPage`) navega para uma página própria com nome, categoria, preço, ficha técnica em tabela clara e breadcrumb/voltar para `/cardapio`. O modal "Novo Produto" continua existindo só para criação rápida (sem ID ainda) — ao salvar, redireciona para a página do produto recém-criado. O botão "Editar" na lista é removido (redundante com a linha clicável); "Desativar"/"Reativar" continuam na lista (com `stopPropagation`) e passam a existir também na página.
6. **Breadcrumb com suporte a segmento dinâmico**: generalizar `Breadcrumb.tsx`/`buildCrumbs` para reconhecer quando a rota atual é mais profunda que um item direto de `NAV_ITEMS` (não só grupos com `children` estáticos) e montar `Item > <label dinâmico>` usando um label fornecido pela própria página (ex.: nome do produto), via um mecanismo reutilizável (contexto/hook) — não um hack específico do Cardápio, para servir qualquer futura rota `/x/:id`.
7. **Padronizar tabela de Estoque e Movimentos junto com Cardápio**: `EstoquePage.tsx` e `MovimentosPage.tsx` (as duas tabelas, aba Insumos e aba Produtos) migram para o mesmo `components/ui/table.tsx` decidido acima, ao mesmo tempo que `CardapioPage.tsx`, adotando a mesma convenção de alinhamento (colunas numéricas à direita) e o mesmo hover de linha — as três telas passam a ser visualmente idênticas em estrutura.
8. **Aba ativa de Movimentos sincronizada na URL**: a aba "Insumos"/"Produtos" de `/estoque/movimentos` passa a ser um query param (`?tab=insumos` | `?tab=produtos`, via `useSearchParams`) em vez de `useState` local — endereçável, compartilhável, e o botão voltar do navegador desfaz a troca de aba. Sem sub-rota nova nem mudança no modelo de `NAV_ITEMS`/`Breadcrumb` (que hoje só suporta 2 níveis, grupo→filho) — o breadcrumb "Estoque > Movimentos" já funciona hoje e continua igual, a aba é estado de página, não um nível de navegação novo.

## User Stories

1. Como dono do bar, quero buscar "agua" e encontrar "Água Com Gás 500ml", para não achar que o produto não está cadastrado.
2. Como dono do bar, quero que a busca ignore CAIXA ALTA/baixa, para não precisar digitar o nome exatamente como foi cadastrado.
3. Como dono do bar, quero abrir um filtro de categoria que mostra a hierarquia (categoria-pai e suas subcategorias) de forma clara, para filtrar por "Bebidas" inteiro ou só por "Cervejas" sem confundir os dois níveis.
4. Como dono do bar, quero que o filtro de categoria abra ancorado no botão que cliquei, para entender de onde ele veio e não parecer um elemento solto na tela.
5. Como dono do bar, quero expandir/recolher uma categoria-pai no filtro para ver suas subcategorias só quando precisar, para não ter uma lista longa sempre visível.
6. Como dono do bar, quero que o botão de ordenação mostre claramente se está ativo (A→Z) ou não, para não achar que ele está quebrado.
7. Como dono do bar, quero ver a tabela de produtos com visual consistente com o resto do sistema, para não sentir que essa tela é "mais feia" que as outras.
8. Como dono do bar, quero que os botões de ação (Desativar/Reativar) tenham um visual atualizado e consistente, para a tela parecer parte do mesmo produto.
9. Como dono do bar, quero clicar em qualquer parte da linha de um produto e ir para uma página só dele, para ver todos os detalhes sem precisar mirar num botão pequeno.
10. Como dono do bar, quero que a página do produto tenha um jeito claro de voltar para a lista de cardápio, para não me sentir perdido na navegação.
11. Como dono do bar, quero editar a ficha técnica de um produto numa tabela com colunas rotuladas (Insumo | Quantidade | Unidade | Custo | remover), para entender de onde vem o custo de cada insumo sem decifrar uma linha de selects soltos.
12. Como dono do bar, quero continuar podendo criar um produto novo rapidamente num modal simples, para não precisar navegar antes de ter os dados básicos salvos.
13. Como dono do bar, quero que, ao salvar um produto novo, o sistema me leve direto para a página dele, para continuar completando a ficha técnica no mesmo fluxo.
14. Como dono do bar, quero que a ficha técnica dentro do modal de criação rápida também use o layout de tabela (não apenas na página do produto), para ter consistência visual entre os dois lugares onde ficha técnica aparece.
15. Como desenvolvedor, quero um componente `Table`/`TableHeader`/`TableBody`/`TableRow`/`TableHead`/`TableCell` reutilizável em `components/ui/`, para não reescrever `<table>` cru em cada tela nova.
16. Como desenvolvedor, quero que esse componente de tabela siga o padrão shadcn (Tailwind, `cn()`, `React.forwardRef`) já usado nos outros componentes de `components/ui/`, para manter a stack consistente (sem adicionar MUI/DataGrid como dependência nova).
17. Como dono do bar, quero que a paginação da tabela de produtos deixe eu escolher quantos itens ver por página (não fixo em 10), para adequar a lista ao meu fluxo de trabalho.
18. Como desenvolvedor, quero que o componente de paginação existente (`components/ui/pagination.tsx`) ganhe um seletor de itens-por-página, para reaproveitar o componente em vez de duplicar lógica de paginação.
19. Como dono do bar, quero que todas essas mudanças respeitem `prefers-reduced-motion` (popover, transições de tabela, navegação para a página do produto), para não sentir desconforto se tiver sensibilidade a movimento.
20. Como dono do bar, quero que o filtro de categoria e a busca continuem funcionando juntos (filtrar por categoria E buscar por nome ao mesmo tempo), para refinar a lista em mais de uma dimensão.
21. Como dono do bar, quero que produtos inativos continuem aparecendo no filtro "Inativos"/"Todos" mesmo com a nova busca normalizada, para não perder a visibilidade que já existe hoje.
22. Como desenvolvedor, quero que a navegação para `/cardapio/:id` seja uma rota real (não um estado de UI), para poder linkar/compartilhar a URL de um produto específico.
23. Como dono do bar, quero ver "Cardápio > Água Com Gás 500ml" no breadcrumb ao abrir a página de um produto, para saber onde estou e como voltar, igual já acontece em Estoque.
24. Como desenvolvedor, quero que o mecanismo de breadcrumb dinâmico seja genérico (não hardcoded pra Cardápio), para reaproveitar em qualquer página futura de detalhe (`/x/:id`) sem duplicar lógica.
25. Como dono do bar, quero que a tabela de Estoque tenha a mesma cara da tabela de Cardápio (mesmo alinhamento de números, mesmo espaçamento), para não sentir que são duas telas de sistemas diferentes.
26. Como desenvolvedor, quero migrar `EstoquePage.tsx` para `components/ui/table.tsx` no mesmo esforço desta spec, para não deixar a inconsistência apontada sem correção enquanto o componente novo já existe.
27. Como dono do bar, quero que o botão "Editar" suma da lista de produtos, para não ter dois jeitos diferentes (linha clicável + botão) de chegar no mesmo lugar.
28. Como dono do bar, quero que o expand inline de ficha técnica na lista suma, para não ver a mesma informação duplicada entre a lista e a página do produto.
29. Como dono do bar, quero poder desativar/reativar um produto direto na página dele, para não precisar voltar pra lista só pra isso.
30. Como dono do bar, quero que o filtro de categoria lembre quais categorias-pai eu tinha expandido enquanto estou na tela de Cardápio, para não expandir tudo de novo cada vez que abro o filtro.
31. Como dono do bar, quero que o breadcrumb não pisque um texto de carregamento enquanto o nome do produto ainda não chegou, para a navegação parecer estável.
32. Como dono do bar, quero que a tabela nova destaque a linha ao passar o mouse, para saber que aquela linha é clicável (Cardápio) ou só pra facilitar leitura (Estoque).
33. Como desenvolvedor, quero que o termo "Produto" esteja definido em `CONTEXT.md`, para ter um vocabulário fechado antes de construir a página dedicada em torno dele.
34. Como dono do bar, quero que as tabelas de Insumos e Produtos em `/estoque/movimentos` tenham o mesmo alinhamento numérico das outras tabelas do sistema, para não notar mais uma tela com convenção diferente.
35. Como dono do bar, quero copiar/compartilhar o link da aba "Produtos" de Movimentos e a pessoa que abrir cair direto nela, para não precisar explicar "clica em Produtos depois de abrir".
36. Como dono do bar, quero que o botão voltar do navegador desfaça a troca de aba em Movimentos, para a navegação se comportar do jeito que eu já espero de um browser.
37. Como desenvolvedor, quero que a URL de Movimentos use um query param pra aba ativa (não uma sub-rota nova), para não precisar estender o modelo de navegação (`NAV_ITEMS`) pra um 3º nível só por causa de duas abas.

## Implementation Decisions

- **Busca normalizada**: normalizar via `.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()` tanto o termo de busca quanto `produto.nome` antes de comparar com `.includes()`. Sem biblioteca nova.
- **Filtro de categoria — popover com árvore expansível**:
  - Novo componente de filtro (local a `features/cardapio/`, escopo restrito como o `DashboardCard` do handoff anterior — não promovido a `components/ui/` ainda).
  - Baseado em Radix Popover (já disponível via shadcn no projeto, verificar dependência existente antes de instalar) ancorado no botão trigger (`transform-origin` no trigger).
  - Estrutura de dados: reusa `useCategorias`/`Categoria[]` (árvore já existe, ver `buildCategoryPaths`/`collectIds` em `CardapioPage.tsx` — lógica de coleta de IDs por categoria-pai continua válida).
  - Categoria-pai com estado expandido/colapsado local (`Set<number>`), subcategoria só renderiza quando pai expandido. Estado de expansão persiste em `useState` no componente pai (`CardapioPage`) enquanto a página estiver montada — sobrevive a fechar/reabrir o popover, não precisa sobreviver a reload de página (sem `localStorage`).
  - Seleção de categoria-pai continua incluindo todas as subcategorias (comportamento de `collectIds` mantido). Seleção continua única (uma categoria/subcategoria por vez) — sem multi-seleção nesta spec.
- **Toggle de ordenação**: manter os dois estados existentes (`az` | `original`), mas o rótulo do botão troca de texto conforme o estado: mostra "A→Z" quando inativo (convite pra ativar) e "Z→A" quando ativo (mostra a ação que desfaz, i.e. clicar volta à ordem de cadastro). Sem ícone adicional.
- **Componente de tabela (`components/ui/table.tsx`)**:
  - Portar o padrão shadcn: `Table` (wrapper com `overflow-auto`), `TableHeader`, `TableBody`, `TableFooter`, `TableRow`, `TableHead`, `TableCell`, `TableCaption`, todos via `React.forwardRef` + `cn()` de `@/lib/utils`.
  - **Decisão explícita**: NÃO usar MUI/`@mui/x-data-grid` (variante alternativa cogitada) — projeto já usa Tailwind + shadcn puro, adicionar MUI introduziria um segundo sistema de estilos e um provider de tema paralelo (`ThemeProvider`) sem necessidade.
  - `TableRow` ganha `hover:bg-gray-50` como estilo padrão do componente (não algo que cada tela reimplementa) — precedente: `PlatformTenantsPage` já usa esse hover em linha clicável. Serve tanto de sinal "isso é clicável" (Cardápio) quanto de reforço de leitura (Estoque, que não navega).
  - `CardapioPage.tsx` migra seu `<table>` cru para os novos componentes. A linha expansível de ficha técnica inline (chevron) é removida da lista — informação agora vive só na página do produto (evita duplicar a mesma informação em dois lugares, um deles não editável).
- **Paginação com itens-por-página**: estender `components/ui/pagination.tsx` com um seletor (`<select>` com opções `10/25/50`) — inspirado no `pageSizeOptions` do DataGrid que o usuário validou como boa ideia, mas implementado como controle simples nativo, não dependência nova. Prop nova `porPagina` + `onPorPaginaChange` controlada pelo componente pai (`CardapioPage` guarda o estado, análogo a `pagina` hoje). Valor padrão ao abrir a tela: `10` (mesmo comportamento de hoje pra quem nunca mexeu). Escolha NÃO persiste entre visitas (sem `localStorage`) — volta a `10` a cada vez que a tela é reaberta; se virar pedido real, persistência é spec própria.
- **Página de produto (`/cardapio/:id`)**:
  - Nova rota no router do frontend (`App.tsx`, ao lado de `/cardapio`, mesmo padrão de `/consumo-interno/:consumidorId`).
  - Novo componente `ProdutoPage.tsx` em `features/cardapio/`, reaproveitando `useProdutos`/`useCreateProduto`/`useUpdateProduto` já existentes (`features/cadastros/produtos/useProdutos`).
  - Ficha técnica na página usa a mesma tabela nova de `components/ui/table.tsx` com colunas rotuladas (Insumo | Quantidade | Unidade | Custo | ação de remover).
  - `ProdutoModal.tsx` (criação rápida) permanece para `POST` inicial; ao ter sucesso, navega para `/cardapio/{id}` em vez de só fechar o modal. Edição deixa de abrir modal — clicar na linha do produto na lista navega para a página (precedente: `PlatformTenantsPage` usa `<tr onClick={...}>` navegando pro detalhe, sem botão dedicado). Botões de ação (Desativar/Reativar) na linha usam `stopPropagation` pra não disparar a navegação.
  - Botão "Editar" é removido da lista (redundante com a linha clicável). Desativar/Reativar continuam na lista E passam a existir também na página do produto (evita forçar volta à lista só pra essa ação).
  - Modal de criação também adota a tabela nova para a ficha técnica (consistência visual entre os dois lugares — user story 14).
- **Motion (ver `apple-design`)**: popover nasce/fecha ancorado no trigger (spatial consistency), sem scrim (não bloqueia fluxo); navegação para página de produto sem exigir spring elaborado (não é gesto físico); cross-fade curto (150–200ms) ao inserir/remover linha de ficha técnica; tudo com fallback `prefers-reduced-motion` (cross-fade em vez de slide/spring).
- **Breadcrumb dinâmico**:
  - Corrigir `buildCrumbs` em `Breadcrumb.tsx`: hoje qualquer item direto (`item.to` sem `children`) retorna `[]` incondicionalmente. Mudar para: se `pathname === item.to` exato, continua sem breadcrumb (página raiz); se `pathname` for mais profundo (`pathname.startsWith(item.to + "/")`), montar `[{ label: item.label, to: item.to }, { label: <dinâmico> }]`.
  - O label dinâmico não existe em `NAV_ITEMS` (é o nome do produto, carregado via API pela própria página) — introduzir um mecanismo reutilizável: um contexto (`BreadcrumbContext`) provido em `AppLayout.tsx`, com um hook (ex. `useBreadcrumbLabel(label: string | undefined)`) que qualquer página de detalhe chama (`useEffect`) para registrar seu label atual; `Breadcrumb.tsx` lê esse valor do contexto quando monta o segmento dinâmico.
  - `ProdutoPage.tsx` chama `useBreadcrumbLabel(produto?.nome)` assim que os dados carregam; limpa (`undefined`) ao desmontar.
  - Esse mecanismo fica genérico o suficiente para qualquer futura rota `/x/:id` reaproveitar sem duplicar lógica (user story 24) — não é um `if pathname.includes("cardapio")` hardcoded.
  - Enquanto `produto?.nome` ainda não carregou (fetch em andamento) ou o produto não existe (404), o breadcrumb mostra só `Cardápio` (sem o segmento dinâmico, sem placeholder tipo "...") — evita "piscar" texto. A página em si é responsável por mostrar seu próprio estado de erro/carregamento no corpo.
  - **Fora de escopo desta spec**: `/consumo-interno/:consumidorId` já é uma rota dinâmica dentro do `AppLayout` com o mesmo problema (breadcrumb hoje mostra só "Vendas > Consumo Interno" estático, não o nome do consumidor) — não usa o novo mecanismo nesta spec; retrofit registrado como próximo passo natural, mesmo raciocínio das outras tabelas não migradas.
- **Padronização de tabela Cardápio + Estoque + Movimentos**:
  - `EstoquePage.tsx` e `MovimentosPage.tsx` (ambas as tabelas: aba Insumos e aba Produtos) migram para os mesmos componentes `Table`/`TableHeader`/`TableBody`/`TableRow`/`TableHead`/`TableCell` de `components/ui/table.tsx` (mesmo componente decidido para Cardápio, ver decisão acima) — mesmo esforço, mesmo PR/commit lógico.
  - Convenção de alinhamento fixada por essas telas: colunas de texto (nome/categoria/item/produto/comanda/status/tipo) alinhadas à esquerda; toda coluna numérica/monetária (preço, custo, estoque, valores, quantidade, saldo) alinhada à direita — `EstoquePage.tsx` quebra essa regra em `Estoque atual`/`Reservado`/`Disponível`/`Custo médio`, `MovimentosPage.tsx` quebra em `Quantidade`/`Preço unit.`/`Subtotal`/`Saldo após` (todos hoje alinhados à esquerda) — ambas corrigidas para ficar consistente com Cardápio.
  - Comportamento existente é preservado — só a estrutura de marcação (`<table>` cru → componentes) e o alinhamento mudam, não a lógica de negócio: Estoque mantém linha destacada em laranja/`bg-orange-50` para item crítico e valores negativos em vermelho; Movimentos mantém badges de tipo coloridos (`TIPO_BADGE`), cor verde/vermelho por entrada/saída, e linha riscada (`line-through`) pra movimento cancelado.
- **Aba de Movimentos via query param**:
  - `MovimentosPage.tsx` troca o `useState` da aba ativa por `useSearchParams` (`?tab=insumos` default, `?tab=produtos`) — trocar de aba chama `setSearchParams`, lendo o valor inicial de `searchParams.get("tab")` com fallback pra `"insumos"`.
  - Filtros de cada aba (item/produto, tipo, datas) continuam como estão hoje (estado local por aba) — só a aba ativa em si vira parte da URL, não os filtros dentro dela (fora de escopo sincronizar filtros na URL nesta spec).

## Testing Decisions

- Testes devem cobrir comportamento externo (busca encontra produto com acento diferente, filtro por categoria-pai inclui subcategorias, paginação muda itens por página), não detalhes de implementação do componente de tabela em si.
- **Frontend**: primeiro teste RTL do projeto (mesma decisão já registrada no handoff do dashboard) — `frontend/src/features/cardapio/CardapioPage.test.tsx` cobrindo: busca normalizada, filtro de categoria com subcategoria, paginação com troca de itens-por-página. Prior art de mock de hook: `frontend/src/features/platform/usePlatformApi.test.tsx`.
- Novo `frontend/src/features/cardapio/ProdutoPage.test.tsx` cobrindo navegação, renderização de ficha técnica em tabela e o breadcrumb dinâmico mostrando o nome do produto.
- `components/ui/table.tsx` não precisa de teste próprio (componente de apresentação puro, sem lógica) — comportamento é coberto indiretamente pelos testes de `CardapioPage`/`ProdutoPage`/`EstoquePage`.
- Novo teste (ou extensão de existente) para `Breadcrumb.tsx`/`buildCrumbs` cobrindo: item direto sem sub-rota (sem breadcrumb, comportamento atual preservado), item direto com sub-rota profunda (`Cardápio > <label dinâmico>`), grupo com `children` estático (comportamento atual do Estoque preservado).
- Estender testes de `EstoquePage` (se existirem) para cobrir a migração de markup sem quebrar comportamento (linha crítica destacada, valores negativos em vermelho).
- Estender/criar testes de `MovimentosPage` cobrindo: troca de aba reflete no query param e vice-versa (URL com `?tab=produtos` abre direto na aba certa), migração de markup preservando badges de tipo e linha riscada de cancelado.
- Sem mudança de backend nesta spec — nenhum teste backend novo necessário.

## Out of Scope

- Retrofit de `/consumo-interno/:consumidorId` (rota dinâmica existente com o mesmo problema de breadcrumb estático) para usar `useBreadcrumbLabel` — o mecanismo nasce genérico nesta spec, mas só é aplicado em Cardápio agora.
- Seleção múltipla de categorias no filtro (continua seleção única, como hoje).
- Persistência (localStorage) da escolha de itens-por-página ou do estado de expansão do filtro de categoria entre sessões — ambos ficam válidos só enquanto a página está montada nesta spec.
- Sincronizar os filtros internos de cada aba de Movimentos (item/produto, tipo, datas) na URL — só a aba ativa entra na URL nesta spec.
- Sub-rotas reais para as abas de Movimentos (`/estoque/movimentos/insumos`, `/produtos`) — decisão explícita de usar query param em vez de estender o modelo de `NAV_ITEMS` pra 3 níveis.
- Migrar as demais ~19 telas do sistema que usam `<table>` cru (compras, relatórios, cadastros, platform, consumo interno, configurações/usuários) para `components/ui/table.tsx` — escopo desta spec é só Cardápio + Estoque, as duas telas comparadas na discussão. Registrar como próximo passo natural depois que o componente estiver validado em produção nessas duas.
- Adicionar classificação de estoque "alto"/excesso (decisão já registrada como recusada no handoff anterior).
- Card "Saídas Hoje" (já recusado anteriormente, não relacionado a esta spec mas registrado para não ressurgir).
- Histórico de preço ou imagem de produto na página `/cardapio/:id` — a página nasce só com os campos que já existem hoje (nome, categoria, preço, ficha técnica); crescer o conteúdo da página é decisão futura, não desta spec.
- Popover de árvore de categoria não é promovido a componente genérico de `components/ui/` nesta spec — fica local a `features/cardapio/` (YAGNI, mesmo raciocínio do `DashboardCard` no handoff do dashboard).
- Qualquer biblioteca de tabela de terceiros (MUI DataGrid, TanStack Table, etc.) — decisão explícita de portar o padrão shadcn simples em vez disso.

## Further Notes

Esta spec nasceu de uma sessão de discussão sobre a aba `/cardapio` (sem código escrito ainda), incluindo:
- Revisão de screenshots da tela atual (filtro de categoria flat, modal de criação apertado, ficha técnica sem cabeçalho de tabela).
- Aplicação pontual de princípios de `apple-design`: usado só para popover (ancoragem espacial), estados de toggle (familiaridade) e página vs. modal (materiais/scrim) — explicitamente **não** aplicado motion de gesto físico (drag/flick/rubber-band), pois nada aqui envolve gesto — evitar over-engineering.
- Usuário avaliou três variantes de componente de tabela sugeridas externamente (shadcn `table.tsx` puro, MUI DataGrid, MUI DataGrid com Tailwind): decisão final foi shadcn puro + gerenciamento de itens-por-página (a única parte do DataGrid que o usuário validou como boa ideia) implementado nativamente, sem adicionar `@mui/material`/`@mui/x-data-grid` como dependência.
- Página de produto dedicada foi decisão explícita do usuário (custo justificado) em vez de só melhorar o modal.
- Nenhuma decisão de backend nesta spec — todos os dados (produto, categoria, ficha técnica) já existem via `useProdutos`/`useCategorias`/`useInsumos`.
- Frentes 6 e 7 (breadcrumb dinâmico, tabela de Estoque) nasceram de uma comparação visual entre `/cardapio` e `/estoque` feita pelo usuário depois da primeira versão desta spec — 22 telas do app usam `<table>` cru hoje; usuário decidiu explicitamente restringir esta spec a Cardápio + Estoque (as duas comparadas) e não fazer a migração completa agora, para não inflar o escopo além do que foi discutido.
- Sessão de grill (`grilling` + `domain-modeling`) rodou sobre esta spec antes da implementação, cobrindo 13 decisões: termo "Produto" (fechado e já escrito em `CONTEXT.md`), gatilho de navegação lista→página (linha clicável, precedente `PlatformTenantsPage`), remoção do botão "Editar" e do expand inline de ficha técnica na lista, escopo do retrofit de breadcrumb (só Cardápio agora), comportamento de loading/404 do breadcrumb dinâmico, ação Desativar/Reativar também na página, hover padrão da tabela nova, default e não-persistência da paginação, persistência de sessão (não localStorage) do expand do filtro de categoria, seleção única no filtro, e afordância exata do toggle A→Z ("A→Z"/"Z→A" por texto, sem ícone).
- `CONTEXT.md` ganhou a entrada "Produto" nesta sessão — termo não existia no glossário antes, apesar de já ser usado pelo código e por outras entradas (Ficha Técnica, CMV) que o referenciam.
- Frentes 8 e "Aba de Movimentos via query param" nasceram de o usuário notar que `/estoque/movimentos` também é uma lista com o mesmo problema de alinhamento, e perguntar se a aba ativa (hoje `useState` local, não refletida na URL) deveria virar sub-rota. Decisão: query param, não sub-rota — evita estender `NAV_ITEMS`/`Breadcrumb` pra um 3º nível de hierarquia só por causa de duas abas de uma mesma tela; usuário confirmou escopo maior (3 tabelas migrando: Cardápio, Estoque, Movimentos) em vez de deixar Movimentos pro "próximo passo".
