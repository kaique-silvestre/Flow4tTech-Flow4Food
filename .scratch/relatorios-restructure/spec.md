Status: ready-for-agent

# Reestruturação de Relatórios (Matchpoint)

## Problem Statement

`/relatorios/vendas`, `/relatorios/compras` e `/relatorios/financeiro` hoje são 3 rotas diferentes que renderizam **a mesma** `RelatoriosIndexPage` — um grid de 10 cards sem nenhum filtro por categoria. Nenhum dos 10 relatórios existentes é de compras, então a aba "Compras" do menu é um beco sem saída. Dentro dos 10, há duplicação real de dado: "Vendas do Dia" e "Fechamento de Caixa" retornam quase os mesmos campos (Fechamento é um subconjunto sem a lista de comandas), e "Produtos Mais Vendidos"/"Vendas por Produto" também (mesmos campos produto/categoria/quantidade/faturamento, com campos-bônus diferentes). Nenhuma das 10 páginas tem export, skeleton de loading consistente ou explicação do que o relatório mostra — cada uma foi construída com date picker cru e layout próprio, sem padrão compartilhado (diferente do que já foi estabelecido no Dashboard com `DashboardCard`).

## Solution

1. Fundir os 2 pares de relatórios duplicados, reduzindo de 10 para 8 relatórios existentes.
2. Adicionar 3 relatórios novos usando dado que já existe no backend mas nunca foi exposto: **Compras por Fornecedor**, **Histórico de Preço de Insumo** (ambos de `Compra`/`ItemCompra`) e **Descontos por Promoção** (de `ItemComanda.promocao_id`). Total final: **11 relatórios**.
3. Reorganizar `RelatoriosIndexPage` numa página única com headers de seção "Vendas" / "Compras" / "Financeiro" agrupando os 11 cards. As 3 rotas do menu continuam existindo e continuam levando pra essa mesma página, mas cada uma faz scroll/âncora até o header correspondente.
4. Criar um layout compartilhado `RelatorioPageLayout` (filtro de data unificado, skeleton, export CSV, botão "?" com popover explicando o relatório) reusado pelas 11 páginas de relatório — mesmo padrão de "?" já estabelecido no Dashboard (`DashboardCard`/`Popover`).

## Distribuição Final por Seção

**Vendas** (6):
1. Fechamento de Caixa *(fusão: Vendas do Dia + Fechamento de Caixa)*
2. Histórico de Comandas
3. Vendas por Garçom
4. Produtos *(fusão: Produtos Mais Vendidos + Vendas por Produto)*
5. Pico de Vendas por Horário
6. **Descontos por Promoção** *(novo)*

**Compras** (2):
7. **Compras por Fornecedor** *(novo)*
8. **Histórico de Preço de Insumo** *(novo)*

**Financeiro** (3):
9. DRE
10. CMV por Produto
11. Perdas e Cortesias

Persona: tanto dono de bar (decisão rápida) quanto contador/gerente (análise mais formal, precisa exportar) — por isso export CSV entra no escopo, não é opcional.

## User Stories

1. Como dono de bar, quero ver os 11 relatórios agrupados por o que eles realmente cobrem (vendas/compras/financeiro), sem ter que adivinhar por que "Compras" mostrava os mesmos relatórios de vendas.
2. Como dono de bar, quero fechar o caixa de um período (não só de um dia) num único relatório, sem precisar abrir duas páginas quase iguais.
3. Como dono de bar, quero ver ranking de produto com todos os campos relevantes (quantidade, receita, %receita, ticket médio, cortesias) num só lugar, sem alternar entre duas páginas quase iguais.
4. Como dono de bar, quero ver quanto gastei por fornecedor num período, para saber onde concentro a compra e negociar melhor.
5. Como dono de bar, quero ver o histórico de preço de um insumo ao longo do tempo, para notar quando um fornecedor started cobrando mais caro.
6. Como dono de bar, quero ver quantas vezes cada promoção foi usada e quanto de desconto ela custou no total, para saber se a promoção compensa.
7. Como contador/gerente, quero exportar qualquer relatório tabular em CSV, para levar o dado pra minha própria planilha/sistema contábil.
8. Como usuário de qualquer papel, quero clicar em "?" em qualquer relatório e entender o que ele mostra e de onde vem o dado, sem perguntar pro time técnico.
9. Como usuário, quero que os 3 itens do submenu "Relatórios" (Vendas/Compras/Financeiro) me levem pra seção certa da página, mantendo a familiaridade da navegação atual.
10. Como desenvolvedor, quero que as fusões reusem os schemas/queries já existentes (agregando os campos que faltam) em vez de duplicar lógica de agregação.
11. Como desenvolvedor, quero testes cobrindo os 3 relatórios novos e as 2 fusões antes de considerar a spec completa.

## Implementation Decisions

### Fusão: Fechamento de Caixa (era Vendas do Dia + Fechamento de Caixa)

- Vira **range de datas** (não mais só 1 dia) — decisão do grill, motivada por "fechar vários dias de uma vez".
- Schema final = superset de `VendasDoDiaResponse` (que já tem a lista de `comandas`) trocando `data: date` por `data_inicio`/`data_fim`, reagregando com o range em vez de 1 dia.
- Endpoint: reaproveita `relatorio_service` — renomear/estender a função que hoje serve `vendas_do_dia` para aceitar range (mesma assinatura de range já usada por `vendas_por_garcom`/`produtos_mais_vendidos`). Remove o endpoint `fechamento-caixa` e a função `fechamento_caixa()` dedicada (ela já é redundante com `_build_por_metodo` de `vendas_do_dia` uma vez que o range cobre o caso de 1 dia).
- Rota nova: `/relatorios/fechamento-caixa` (mantém o nome mais claro pro caso de uso "fechar caixa"). Rota antiga `/relatorios/vendas-do-dia` deixa de existir — atualizar `App.tsx`/`RelatoriosIndexPage`/qualquer link interno.
- **Risco de performance**: a lista de `comandas` por comanda individual pode ficar grande num range de 30 dias (diferente do caso de 1 dia). Decisão: manter a lista completa por ora (sem paginação) — já existe `HistoricoComandasPage` com paginação pra esse caso de uso de "ver comanda por comanda" num range grande; Fechamento de Caixa é pra períodos curtos (1-7 dias) na prática. Não adicionar paginação nesta spec; se ficar lento em produção, é spec própria.

### Fusão: Produtos (era Produtos Mais Vendidos + Vendas por Produto)

- Schema final = union dos campos das duas: `produto_id`, `produto_nome`, `categoria_nome`, `quantidade_total` (renomear de `qtd_vendida`/`quantidade_total` — usar um nome só), `qtd_cortesias`, `receita_total` (renomear de `faturamento`), `percentual_receita`, `ticket_medio`.
- Ordenação default: por `receita_total` desc (decisão já confirmada). Range de datas, default 30 dias (mesmo default das duas páginas originais).
- Endpoint único `/relatorios/produtos` reaproveitando a query mais completa das duas (`vendas_por_produto` já calcula `qtd_cortesias`/`ticket_medio`; `produtos_mais_vendidos` já calcula `percentual_receita` — juntar as duas queries/CTEs num só service, sem duplicar cálculo de faturamento por produto). Remove `/relatorios/produtos-mais-vendidos` e `/relatorios/vendas-por-produto`.

### Novo: Compras por Fornecedor

- Fonte: `Compra` (`fornecedor_id`, `data_compra`, `total`, `status`). Filtro por range de `data_compra`. **Exclui `status == "cancelado"`** (decisão: compra cancelada não é gasto real).
- Agregação por `fornecedor_id`: `fornecedor_nome`, `qtd_compras`, `total_gasto` (soma de `Compra.total`), `ticket_medio_compra`.
- Novo schema `CompraPorFornecedorItem` + `ComprasPorFornecedorResponse` (`data_inicio`, `data_fim`, `total_geral`, `fornecedores: list[...]`), novo endpoint `GET /relatorios/compras-por-fornecedor`, nova função em `relatorio_service.py` (reusa join com `Fornecedor` já usado em `compras_repository.py` para o nome).

### Novo: Histórico de Preço de Insumo

- Fonte: `ItemCompra` (`insumo_id`, `custo_unitario`, `quantidade`) join `Compra` (`data_compra`, `fornecedor_id`) join `Fornecedor` (nome).
- Filtro: **seleciona 1 insumo** (dropdown, reusa a listagem de insumos já existente em `/cadastros/insumos`) + range de datas. Retorna lista cronológica: `data_compra`, `custo_unitario`, `quantidade`, `fornecedor_nome`.
- Novo schema `HistoricoPrecoInsumoItem` + `HistoricoPrecoInsumoResponse` (`insumo_id`, `insumo_nome`, `itens: list[...]`), novo endpoint `GET /relatorios/historico-preco-insumo?insumo_id=&data_inicio=&data_fim=`.
- Layout: gráfico de linha (Recharts, já usado no Dashboard) com `custo_unitario` no eixo Y — não lista/tabela como os outros, porque o ponto é ver a tendência.

### Novo: Descontos por Promoção

- Fonte: `ItemComanda` com `promocao_id IS NOT NULL`, excluindo `cancelado=True`/`estornado=True` (mesmo padrão de filtro já usado pelos outros relatórios de venda). Join com `Promocao` pra nome/tipo de desconto.
- **Limitação conhecida e aceita**: `ItemComanda` guarda só o `preco_unitario` já aplicado (com desconto), não guarda o preço original no momento da venda. O valor do desconto por item é recalculado a partir de `Promocao.tipo_desconto`/`valor_desconto` **atuais** (percentual → `preco_unitario / (1 - valor_desconto/100) - preco_unitario`; valor_fixo → `valor_desconto` por unidade). Se a promoção foi editada depois de usada, o valor recalculado pode não bater exatamente com o desconto real dado na hora — documentar essa limitação no popover "?" do relatório ("valor estimado com a configuração atual da promoção"). Corrigir isso de verdade exigiria um `preco_original`/`valor_desconto_aplicado` snapshot em `ItemComanda`, que é migration nova — fora de escopo aqui.
- Agregação por `promocao_id`: `promocao_nome`, `qtd_usos` (count de itens), `quantidade_total`, `valor_desconto_total`.
- Novo schema `DescontoPromocaoItem` + `DescontosPorPromocaoResponse` (`data_inicio`, `data_fim`, `total_geral`, `promocoes: list[...]`), novo endpoint `GET /relatorios/descontos-por-promocao`.

### Frontend: `RelatoriosIndexPage`

- Página única (as 3 rotas continuam montando o mesmo componente). Cada seção é um `<section id="vendas">`/`id="compras">`/`id="financeiro">` com header (`<h2>`) e o grid de cards da seção. Ao navegar pra `/relatorios/compras`, a página faz `scrollIntoView({ behavior: "smooth" })` no elemento da seção correspondente (respeitar `prefers-reduced-motion`: `behavior: "auto"` se reduzido).
- `RELATORIOS` (array de cards) ganha campo `secao: "vendas" | "compras" | "financeiro"` e é reagrupado antes de renderizar.

### Frontend: `RelatorioPageLayout` (novo componente compartilhado)

- Local: `frontend/src/features/relatorios/components/RelatorioPageLayout.tsx` (mesmo padrão de escopo local usado pelo `DashboardCard` — promover pra `components/ui/` só se uma 3ª feature precisar).
- Props: `titulo`, `helpText` (pro popover "?", reusa `Popover`/`PopoverTrigger`/`PopoverContent` de `@/components/ui/popover.tsx`, mesmo spring sem bounce documentado na spec do dashboard), filtro de data (variante `single` — 1 date input — ou `range` — 2 date inputs — declarada por prop, com default de range de 30 dias onde já existia), `loading` (renderiza skeleton — cross-fade, nunca slide, mesmo padrão do dashboard), `onExportCsv` (opcional; quando presente mostra botão "Exportar CSV" no canto superior).
- Export CSV: **client-side**, sem endpoint novo — função utilitária `exportToCsv(rows: Record<string, unknown>[], filename: string)` em `frontend/src/lib/csv.ts`, gera Blob e usa `<a download>` (funciona no browser real do usuário; não confundir com o bloqueio de download de artifacts — isso aqui é o app rodando localmente, não um artifact). Cada página de relatório passa as linhas já formatadas (mesmos dados exibidos na tabela).
- As 11 páginas de relatório passam a usar `RelatorioPageLayout` em vez de montar filtro/skeleton próprios — refatoração mecânica nas 8 páginas existentes (6 mantidas + 2 fusões) + 3 novas.

## Testing Decisions

- Seam backend: `backend/tests/test_relatorios_financeiros.py` (prior art de fixtures `_criar_produtos_com_ficha`, `_set_custo_medio`) ganha casos novos:
  - Fechamento de Caixa com range de datas cobrindo múltiplos dias (soma corretamente pagamentos/comandas de mais de 1 dia — hoje só é testado com 1 dia).
  - Produtos (fusão): todos os campos do union presentes e corretos, ordenado por `receita_total` desc.
  - Compras por Fornecedor: soma correta por fornecedor, excluindo compra com `status="cancelado"`.
  - Histórico de Preço de Insumo: ordenação cronológica correta, filtro por 1 insumo não traz custo de outro insumo.
  - Descontos por Promoção: cálculo do valor de desconto pra `tipo_desconto="percentual"` e `"valor_fixo"`, excluindo item cancelado/estornado.
- Seam frontend: estender o padrão RTL já estabelecido pelo Dashboard (`DashboardPage.test.tsx`) pro `RelatorioPageLayout` — casos mínimos: (a) botão "?" abre popover com `helpText`; (b) botão "Exportar CSV" só aparece quando `onExportCsv` é passado; (c) skeleton renderiza durante `loading=true`.
- Não é necessário E2E novo (mesma decisão já tomada na spec do Dashboard — sem suite E2E no projeto hoje).

## Out of Scope

- `preco_original`/`valor_desconto_aplicado` snapshot em `ItemComanda` (corrigiria a limitação de Descontos por Promoção retroativamente) — migration nova, spec própria se o dono precisar de precisão histórica exata.
- Paginação da lista de comandas em Fechamento de Caixa pra ranges longos — só se virar problema real de performance em produção.
- Export em PDF — só CSV nesta spec.
- Categorização de relatório configurável pelo usuário (mover card de seção) — distribuição é fixa no código por ora.
- Qualquer relatório de estoque (perdas por vencimento vs ficha técnica, consumo interno) — levantado durante a investigação de lacunas, mas não pedido nesta spec.
- Novo endpoint pra promoção (já usa dado existente sem alterar `promocoes.py`).

## Rotas removidas (sem redirect)

`/relatorios/vendas-do-dia`, `/relatorios/produtos-mais-vendidos`, `/relatorios/vendas-por-produto` deixam de existir, substituídas por `/relatorios/fechamento-caixa` e `/relatorios/produtos`. **Decisão do usuário**: sem `<Navigate>` de compatibilidade — só links internos do próprio app apontam pra essas rotas, e serão atualizados junto (menu, `RelatoriosIndexPage`).

## Further Notes

- Achados de overlap confirmados por leitura direta de `frontend/src/features/relatorios/*.tsx` + `backend/src/schemas/relatorio_schemas.py`: `VendasDoDiaResponse` já é superset de `FechamentoCaixaResponse` (mesmos campos + `comandas`); `ProdutosMaisVendidoItem` e `VendasPorProdutoItem` cobrem o mesmo grão (produto/categoria/quantidade/faturamento) com campos-bônus complementares (`percentual_receita` vs `qtd_cortesias`+`ticket_medio`).
- Dado novo confirmado direto no model: `backend/src/models/compras.py` (`Compra.fornecedor_id/total/status`, `ItemCompra.custo_unitario`) e `backend/src/models/itens_comanda.py:35` (`promocao_id`) — nenhum dos dois tinha relatório expondo isso antes desta spec.
- Nenhuma das 10 páginas atuais tinha export CSV nem skeleton consistente — confirmado por grep (`CSV` não aparece em nenhum arquivo de `features/relatorios/`).
- **Correção de registro**: uma rodada anterior de análise (subagente) escreveu uma versão preliminar deste arquivo afirmando "grill de 4 rounds com decisões do usuário" — isso não aconteceu; foi uma proposta técnica do subagente, não uma decisão validada. As decisões reais foram tomadas em 4 rounds de grill diretamente com o usuário nesta conversa (skill `grilling`), todas aceitando a recomendação proposta sem contestação: fundir os 2 pares duplicados com range de datas; incluir os 3 relatórios novos (Compras por Fornecedor, Histórico de Preço de Insumo, Descontos por Promoção — este último com aviso de limitação no popover "?"); manter as 3 rotas do menu com scroll-to-section; criar `RelatorioPageLayout` compartilhado refatorando as 11 páginas; export CSV client-side; remover rotas antigas sem redirect (só links internos); estoque/PDF/categorização configurável ficam fora de escopo.
