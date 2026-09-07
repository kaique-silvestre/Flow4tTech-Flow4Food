# Orchestration tracker — restructure issues (auto, one-by-one via subagent)

Sidebar excluído (em andamento manual). Ordem por dependência: cardapio (Table primitive)
desbloqueia cadastros e gestao-usuarios. dashboard/relatorios ainda sem issues quebradas.

Regra: 1 issue por rodada de subagente. Commit por issue. Marcar [x] aqui e no arquivo da issue
ao concluir. CHANGELOG.md sempre atualizado (Autor: Kaique Gonzaga Silvestre <kaique.silvestre.22@gmail.com>).

## Fase A — cardapio-restructure
- [x] 01-table-primitive-cardapio (commit eadd1bd)
- [x] 02-busca-normalizada (commit 25b0387)
- [x] 03-toggle-ordenacao (commit e14752c)
- [x] 04-paginacao-itens-por-pagina (commit 39dac8e)
- [x] 05-filtro-categoria-popover (commit 443ca56)
- [x] 06-produto-page-breadcrumb-dinamico (commit 6a28b59)
- [x] 07-migrar-tabela-estoque (commit eccda30)
- [x] 08-migrar-tabela-movimentos-tab-query-param (commit 34cee9c) — FASE A COMPLETA

## Fase B — cadastros-restructure (depende de A/01)
- [x] 01-insumos (commit 0b03242)
- [x] 02-fornecedores (commit bd9cfc3)
- [x] 03-garcons (commit f7b9a7e)
- [x] 04-metodos-pagamento (commit 418b8f3)
- [x] 05-garcom-comissoes-modal (commit 88630e9) — FASE B COMPLETA

## Fase C — gestao-usuarios-restructure (depende de A/01)
- [x] 01-tabela-avatar-badge (commit 15e7cb0)
- [x] 02-dropdown-acoes (commit 10e1851)
- [x] 03-protecoes-backend-refletidas (commit 4197046)
- [x] 04-aba-query-param (commit b3769a5) — FASE C COMPLETA

## Fase D — dashboard-restructure
- [x] issues quebradas em .scratch/dashboard-restructure/issues/ (9 tickets)
- [x] 01-fix-nan-percent (commit 6bdd935)
- [ ] 02-backend-novos-campos (fundacional p/ 04-08)
- [ ] 03-dashboard-card-wrapper (fundacional p/ 04-08)
- [ ] 04-widget-formas-pagamento
- [ ] 05-widget-garcons-hoje
- [ ] 06-widget-comissoes-a-pagar
- [ ] 07-widget-cortesias-perdas
- [ ] 08-widget-estoque-atencao
- [ ] 09-top10-produtos-faturamento-cmv

## Fase E — relatorios-restructure (depende de D — usa DashboardCard; issues ainda não quebradas)
- [ ] gerar issues a partir de spec.md
- [ ] (issues a preencher aqui após quebra)

## Log
- 2026-09-07: tracker criado, iniciando Fase A/01.
- 2026-09-07: A/01 concluído (commit eadd1bd). Nota do subagente: graphify-out/graph.json tem backlog de ~162 docs desatualizados (.claude/PRPs/plans/*.md) fora do escopo dos tickets — precisa `graphify --update` completo em algum momento, separado deste loop.
- 2026-09-07: A/02 concluído (commit 25b0387).
- 2026-09-07: A/03 concluído (commit e14752c). Nota: estado inicial de ordenação é "az", não "original" como o texto do ticket 03 assume — pré-existente, fora do escopo, comportamento de label implementado corretamente conforme regra do ticket mesmo assim.
- 2026-09-07: A/04 concluído (39dac8e). A/05 concluído (443ca56). A/06 concluído (6a28b59, ticket maior — nova rota /cardapio/:id + BreadcrumbContext genérico). A/07 concluído (eccda30). A/08 concluído (34cee9c). FASE A COMPLETA.
- 2026-09-07: Nota recorrente dos subagentes: graphify-out/graph.json tem drift grande (500+ arquivos, incluindo ~162 docs .scratch) não relacionado aos tickets — cada subagente rodou update AST-only escopado ao próprio arquivo tocado. Recomendado rodar `graphify --update` completo com LLM fora deste loop, quando o usuário puder revisar custo/tempo.
- 2026-09-07: iniciando Fase B (cadastros-restructure), B/01.
- 2026-09-07: B/01 concluído (0b03242). Nota recorrente: `normalizarTexto` duplicado por página (CardapioPage, InsumosPage) em vez de util compartilhado — considerar extrair para `frontend/src/lib/` numa limpeza pós-loop. Nota: um subagente relatou `graphify-out/` inexistente — inconsistência entre relatos, ignorar por ora (fora do escopo do loop).
- 2026-09-07: B/02 (bd9cfc3), B/03 (f7b9a7e, DropdownMenu + jsdom PointerEvent polyfill novo em GarconsPage.test.tsx), B/04 (418b8f3), B/05 (88630e9) concluídos. FASE B COMPLETA.
- 2026-09-07: iniciando Fase C (gestao-usuarios-restructure), C/01.
- 2026-09-07: C/01 concluído (15e7cb0). C/02 concluído (10e1851) — bug real corrigido: Radix DropdownMenuItem `disabled` não bloqueava `onClick`, item "Desativar"/"Ativar" de Perfil disparava mutation mesmo desabilitado; guard `if (!canToggle) return` adicionado.
- 2026-09-07: C/03 concluído (4197046, proteções de perfil/permissões/proprietário espelhadas do backend). C/04 concluído (b3769a5). FASE C COMPLETA.
- 2026-09-07: iniciando Fase D (dashboard-restructure) — sem issues quebradas ainda, lendo spec.md completo pra criar tickets.
