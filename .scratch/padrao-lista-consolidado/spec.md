Status: ready-for-agent

# Padrão único de tela de lista (Matchpoint) — correção de consistência cross-page

## Problem Statement

As specs `cardapio-restructure`, `cadastros-restructure` e `gestao-usuarios-restructure` foram escritas e implementadas **isoladas por pasta/tela**, sem um contrato único de "como uma lista se parece no sistema". Cada ticket foi implementado fielmente à sua própria spec, mas as specs nunca foram comparadas lado a lado. Resultado: usuário comparou Cardápio, Estoque e Insumos lado a lado e viu 3 telas de listagem com elementos diferentes entre si — filtro de status presente em algumas e ausente em outras, paginação com seletor de itens/página em uma só, ações por linha em botões soltos numas e dropdown em outras, badge de status ausente numa tela que deveria ter.

Esta spec fecha esse buraco: define o contrato único e lista as correções pontuais em cada tela já migrada para bater com ele.

## Contrato único de lista

Toda tela de listagem de entidade cadastrável (tem campo `ativo`) segue:

1. **Filtro de status** — toggle "Ativos"/"Inativos"/"Todos", default "Ativos". Aplica-se a: Cardápio, Insumos, Fornecedores, Garçons, Métodos de Pagamento, Usuários/Perfis, **e Estoque** (decisão desta spec: Estoque ganha o mesmo filtro, aplicado sobre `insumo.ativo`, mesmo sendo uma view de saldo — consistência total decidida pelo usuário). Movimentos (log histórico) **não** ganha — não tem conceito de ativo/inativo, é registro de fato consumado.
2. **Badge de status** — `<Badge variant="outline">` verde "Ativo"/cinza "Inativo" nas mesmas telas do item 1 (exceto Estoque, que já não tem coluna de linha por insumo individual "ativo" visível hoje — badge entra na mesma condição do filtro, ver ticket 05). Linha inativa mantém `line-through` no nome, sem `opacity` extra.
3. **Paginação com itens-por-página** — toda tela paginada usa `components/ui/pagination.tsx` com as props `porPagina`/`onPorPaginaChange` (já existem no componente desde a spec do Cardápio) e o seletor 10/25/50. Nenhuma tela mais usa uma constante `POR_PAGINA` fixa sem seletor.
4. **Ações por linha** — se a linha tem **mais de uma** ação (ex. Editar + Desativar/Ativar), usa um único `DropdownMenu` (`components/ui/dropdown-menu.tsx`). Se a linha tem **só uma** ação (ex. Cardápio, que já navega ao clicar e só resta Desativar/Reativar), um botão simples continua correto — não force dropdown de item único.
5. **Breadcrumb** — toda tela mostra seu próprio label como breadcrumb, mesmo quando é um item direto de `NAV_ITEMS` sem grupo (ex. "Cardápio" sozinho na raiz `/cardapio`). Único item sem breadcrumb: Dashboard (rota `/`, home). Isso muda a regra atual de `buildCrumbs`, que hoje retorna `[]` para qualquer item direto em `pathname === item.to`.

## Correções necessárias (ticket por ticket)

- **Breadcrumb genérico**: `buildCrumbs` para de retornar `[]` em item direto na rota raiz (exceto `/`) — passa a retornar `[{label: item.label}]`. Afeta Cardápio (hoje sem breadcrumb nenhum na raiz) e qualquer outro item direto futuro. Não quebra o mecanismo dinâmico já existente para `/cardapio/:id` (que já monta `[{label, to}, {label: dinâmico}]`).
- **Badge em Cardápio**: `CardapioPage.tsx` não tem coluna de status/badge hoje (só filtra e tacha o nome). Adicionar `<Badge variant="outline">` igual às demais telas de Cadastros.
- **DropdownMenu em Insumos/Fornecedores/Métodos de Pagamento**: as três ainda usam dois botões soltos ("Editar" + "Desativar"/"Ativar"). Unificar em `DropdownMenu`, mesmo padrão já usado em Garçons (`f7b9a7e`) e Gestão de Usuários (`10e1851`) — **atenção ao bug já encontrado e corrigido nesses dois**: `disabled` do Radix `DropdownMenuItem` não bloqueia `onClick` sozinho, sempre adicionar guard explícito (`if (condição) return;`) dentro do handler quando o item pode estar desabilitado (caso de Métodos de Pagamento: item "padrão" não pode desativar/remover).
- **Itens-por-página em Insumos/Fornecedores/Garçons/Métodos de Pagamento/Estoque**: essas 5 telas usam uma constante `POR_PAGINA` fixa (12, 10, 8, 10, 20 respectivamente) sem seletor. Trocar por estado `porPagina` controlado + prop no `Pagination`, mesmo padrão já implementado em `CardapioPage.tsx` (ticket `39dac8e`) e `EstoquePage`/`MovimentosPage` NÃO tinham isso ainda apesar de já estarem na tabela nova — incluir os 5.
- **Filtro Ativos/Inativos/Todos em Estoque**: `EstoquePage.tsx` hoje lista todos os insumos com saldo, sem filtro por `ativo`. Adicionar o mesmo toggle das demais telas, filtrando pela flag `ativo` do insumo (dado já disponível via `useInsumos`/o mesmo hook que a página já consome ou precisa passar a consumir).

## Testing Decisions

- Cobrir cada correção com teste (RTL onde a tela já tem suite; unitário de função pura onde fizer sentido) seguindo o padrão já estabelecido nas specs anteriores (mock de hook estilo `usePlatformApi.test.tsx`).
- Para o guard do Radix `DropdownMenuItem` disabled, replicar o teste de regressão que provou o bug em Gestão de Usuários (clicar no item desabilitado não deve disparar a mutation).

## Out of Scope

- Migrar telas fora deste conjunto (Compras, Relatórios, Categorias, Promoções, Consumo Interno) para o contrato — spec futura, mesma decisão de escopo já registrada nas specs anteriores.
- Unificar o padrão de "linha clicável → página dedicada" do Cardápio nas demais telas (Insumos, Fornecedores, etc. continuam usando modal, não página dedicada) — fora de escopo, decisão não pedida pelo usuário nesta rodada.
