Status: ready-for-agent

# Reestruturação das listas de Cadastros (Matchpoint)

## Problem Statement

`/cadastros/insumos`, `/cadastros/fornecedores`, `/cadastros/garcons` e `/cadastros/metodos-pagamento` são quatro telas de listagem quase idênticas (mesmo esqueleto: filtro Ativos/Inativos/Todos, `<table>` cru, botões de ação por linha), mas divergem em detalhes que deveriam ser iguais:

1. Nenhuma das quatro tem busca por nome — só o filtro de status. Em listas com volume (ex. muitos insumos), sem busca a única forma de achar um item é rolar a página inteira.
2. `InsumosPage.tsx` tem uma coluna numérica ("Estoque") alinhada à esquerda — mesma classe de bug já corrigido em Cardápio/Estoque/Movimentos (`.scratch/cardapio-restructure/spec.md`). `GarcomComissoesModal.tsx` (dentro da feature Garçons) tem o mesmo problema na coluna "Valor".
3. `FornecedoresPage.tsx` marca linha inativa com `opacity-60` + `line-through`; `InsumosPage.tsx`/`GarconsPage.tsx`/`MetodosPagamentoPage.tsx` usam só `line-through` — mesmo estado (`ativo: false`), apresentação visual diferente entre telas.
4. `GarconsPage.tsx` tem três ações por linha (Ver Comissões, Editar, Desativar/Ativar) como botões soltos — o mesmo problema de escala já identificado e resolvido com dropdown em Gestão de Usuários (`.scratch/gestao-usuarios-restructure/spec.md`).
5. `MetodosPagamentoPage.tsx` é a única das quatro **sem paginação** — se a lista crescer, não há como navegar além da primeira tela.
6. `MetodosPagamentoPage.tsx` esconde silenciosamente os botões "Desativar" e "Remover" quando `metodo.padrao === true`, sem nenhuma explicação — o backend já tem a mensagem pronta (`metodos_pagamento_service.py`, 409 "Métodos padrão não podem ser desativados"), mas ela só aparece se alguém magicamente conseguisse clicar num botão que nem existe. Mesmo anti-padrão silencioso já corrigido em Gestão de Usuários (proprietário/perfil).
7. Status (Ativo/Inativo) é um `<span>` inline com classes repetidas em cada uma das quatro telas, em vez do `components/ui/badge.tsx` já instalado e já adotado nas outras specs de padronização.
8. Todas usam `<table>` cru — mesmo componente `components/ui/table.tsx` decidido nas outras duas specs ainda não chegou aqui.

## Solution

Padronizar as quatro telas de Cadastros (e o modal de Comissões de Garçom) nas mesmas frentes já decididas nas specs irmãs (Cardápio+Estoque+Movimentos, Gestão de Usuários), usando os termos do glossário do projeto (Insumo — ver `CONTEXT.md`):

1. **Migrar as quatro tabelas + `GarcomComissoesModal`** para `components/ui/table.tsx`, com a mesma convenção já fixada (texto à esquerda, numérico/monetário à direita, hover de linha).
2. **Adicionar busca normalizada** (mesmo mecanismo do Cardápio: NFD + lowercase, ver spec do Cardápio) nas quatro telas — filtra por nome, funciona junto com o filtro de status existente.
3. **Badge de status** reaproveitando `components/ui/badge.tsx` nas quatro telas, substituindo os `<span>` inline.
4. **Unificar apresentação de linha inativa**: escolher uma convenção única (ver Implementation Decisions) e aplicar nas quatro — hoje Fornecedores diverge das outras três.
5. **Dropdown de ações em `GarconsPage.tsx`** (3 ações: Ver Comissões, Editar, Desativar/Ativar) — mesmo padrão `components/ui/dropdown-menu.tsx` já decidido em Gestão de Usuários. As outras três telas (2 ações cada) permanecem com botões soltos — não há ganho em forçar dropdown para 2 ações.
6. **Adicionar paginação em `MetodosPagamentoPage.tsx`** — mesmo componente `components/ui/pagination.tsx` já usado nas outras três.
7. **Explicar por que "Desativar"/"Remover" não aparecem para o método padrão**: em vez de sumir sem explicação, mostrar os itens desabilitados com texto de apoio — espelha a mensagem que já existe no backend (`"Métodos padrão não podem ser desativados"`), mesmo raciocínio já aplicado às proteções de Usuário/Perfil.

## User Stories

1. Como dono do bar, quero buscar um insumo/fornecedor/garçom/método de pagamento por nome, para não precisar rolar a lista inteira procurando.
2. Como dono do bar, quero que a busca ignore acento e caixa (mesmo comportamento já decidido pro Cardápio), para ter uma experiência de busca consistente em todo o app.
3. Como dono do bar, quero ver a coluna "Estoque" de Insumos alinhada à direita, para ler os números na mesma convenção das outras tabelas do sistema.
4. Como dono do bar, quero ver a coluna "Valor" no modal de Comissões de Garçom alinhada à direita, pela mesma razão.
5. Como dono do bar, quero que um item inativo pareça visualmente igual em qualquer tela do sistema, para não estranhar Fornecedores sendo mais "apagado" que Insumos.
6. Como dono do bar, quero um menu de ações único em Garçons (em vez de três botões soltos), para a linha não ficar apertada em telas menores.
7. Como dono do bar, quero navegar por páginas na lista de Métodos de Pagamento se ela crescer, para não ficar preso rolando uma lista sem fim.
8. Como dono do bar, quero entender por que não consigo desativar ou remover um método de pagamento marcado como padrão, em vez de simplesmente não ver o botão.
9. Como dono do bar, quero que o status Ativo/Inativo tenha a mesma aparência (mesmo componente de badge) em Insumos, Fornecedores, Garçons e Métodos de Pagamento.
10. Como desenvolvedor, quero que as quatro tabelas usem `components/ui/table.tsx`, para não ter uma quinta implementação de `<table>` cru divergente no app.
11. Como dono do bar, quero que o filtro de status e a busca por nome funcionem juntos em cada uma das quatro telas, para refinar a lista em mais de uma dimensão, igual já acontece no Cardápio.

## Implementation Decisions

- **Busca normalizada**: replicar exatamente o mecanismo decidido no Cardápio (`.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()` nos dois lados da comparação) em `InsumosPage.tsx`, `FornecedoresPage.tsx`, `GarconsPage.tsx`, `MetodosPagamentoPage.tsx`. Campo de busca com o mesmo componente `Input` já usado no Cardápio, resetando a página ao digitar (mesmo padrão `setPagina(1)` já usado nos filtros existentes dessas telas).
- **Tabela**: as quatro páginas + `GarcomComissoesModal.tsx` migram para `Table`/`TableHeader`/`TableBody`/`TableRow`/`TableHead`/`TableCell` de `components/ui/table.tsx` (mesmo componente das specs irmãs). Convenção de alinhamento: `Estoque` (Insumos) e `Valor` (modal de Comissões) passam a alinhar à direita; as demais colunas de texto continuam à esquerda.
- **Linha inativa — convenção única**: adotar `line-through` no nome (já é o padrão em 3 das 4 telas) e **remover** o `opacity-60` extra de `FornecedoresPage.tsx` — a maioria já não usa opacity, e a badge de status "Inativo" já comunica o estado sem precisar apagar a linha inteira visualmente.
- **Badge de status**: trocar os `<span className="rounded-full ...">` por `<Badge variant="outline" className="...">` (mesma decisão da spec de Usuários) nas quatro telas.
- **Dropdown de ações em Garçons**: `GarconsPage.tsx` troca os três `Button` soltos (Ver Comissões / Editar / Desativar-Ativar) por um único `DropdownMenu` com esses três itens — mesmo padrão decidido em Gestão de Usuários. Insumos/Fornecedores/Métodos de Pagamento mantêm botões soltos (só 2 ações cada, sem ganho em forçar menu).
- **Paginação em Métodos de Pagamento**: adicionar `useState` de página + `Pagination`/`paginar` de `components/ui/pagination.tsx`, mesmo padrão das outras três telas (tamanho de página a definir pelo desenvolvedor seguindo o precedente — ex. 10, como Fornecedores).
- **Explicar bloqueio de método padrão**: no dropdown ou nos botões de `MetodosPagamentoPage.tsx`, quando `m.padrao === true`, os itens "Desativar" e "Remover" ficam desabilitados (não ausentes) com texto de apoio: "Método padrão não pode ser desativado/removido" — espelha a mensagem já existente em `metodos_pagamento_service.py` (409 "Métodos padrão não podem ser desativados"), sem mudança de backend.

## Testing Decisions

- Testes cobrem comportamento externo: busca encontra item com acento/caixa diferente em cada uma das quatro telas, filtro de status e busca funcionam combinados, coluna numérica alinhada à direita (Insumos, modal de Comissões), dropdown de ações em Garçons mostra os três itens corretos, paginação funciona em Métodos de Pagamento, itens desabilitados de método padrão mostram texto de apoio.
- Estender testes existentes de `InsumosPage`/`FornecedoresPage`/`GarconsPage`/`MetodosPagamentoPage` (se existirem) em vez de criar do zero — seguir padrão de mock já usado nessas telas.
- `components/ui/table.tsx`/`badge.tsx`/`dropdown-menu.tsx`/`pagination.tsx` não precisam de teste próprio nesta spec (já cobertos indiretamente, dois já testados pelas specs irmãs).
- Sem mudança de backend nesta spec — a mensagem de método padrão já existe; é só espelhada no front.

## Out of Scope

- `Categorias` e `Promoções` (as outras duas telas do grupo "Cadastros") — não usam esse padrão de tabela flat hoje (visualização diferente, provavelmente árvore/cards); investigar separadamente se um dia precisarem de padronização.
- Adicionar coluna nova ou dado novo a qualquer uma das quatro tabelas — escopo é só estrutura/apresentação, não conteúdo.
- Mudar o modelo de dados de `MetodoPagamento` (o flag `padrao`, a lógica de qual método é padrão) — só a UI que reflete a regra existente.
- Migrar mais telas além destas quatro + o modal de Comissões — outras `<table>` cru do sistema (relatórios, compras, platform, consumo interno, configurações) continuam registradas como pendência nas specs anteriores.

## Further Notes

Esta spec nasceu de o usuário notar, depois de duas rodadas de padronização (Cardápio+Estoque+Movimentos, Gestão de Usuários), que `/cadastros/insumos`, `/cadastros/fornecedores`, `/cadastros/garcons` e `/cadastros/metodos-pagamento` são "listas do mesmo tipo" que deveriam seguir o mesmo padrão mas não seguem, e pedir investigação profunda.

Achados da investigação (não pedidos explicitamente, descobertos ao ler o código de verdade):
- `GarcomComissoesModal.tsx` tem uma quinta tabela raw escondida dentro da feature Garçons, não visível como "página" mas com o mesmo problema de alinhamento.
- `MetodosPagamentoPage.tsx` é a única das quatro sem paginação — não foi mencionado pelo usuário, achado na leitura.
- `MetodosPagamentoPage.tsx` repete o mesmo anti-padrão de "esconder botão sem explicar" já corrigido em Gestão de Usuários (lá era Proprietário/Perfil; aqui é `padrao`) — o backend já tem a mensagem certa (`metodos_pagamento_service.py:49,61`), só não chega no front.
- `FornecedoresPage.tsx` diverge sozinha das outras três no estilo de linha inativa (`opacity-60` extra) — decisão explícita de alinhar as quatro pelo padrão majoritário (só `line-through`) em vez de escolher arbitrariamente.
- `Categorias`/`Promoções` foram checadas e confirmadas como não usando `<table>` cru — não fazem parte desta família de bug, ficam fora de escopo.
- Terceira spec de padronização de lista nesta sessão — junto com `.scratch/cardapio-restructure/spec.md` (Cardápio, Estoque, Movimentos) e `.scratch/gestao-usuarios-restructure/spec.md` (Usuários, Perfis), todas reaproveitando os mesmos componentes (`Table`, `Badge`, `DropdownMenu`, `Pagination`) sem inflar dependências novas.
