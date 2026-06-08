# Issues — Matchpoint v0.6: Menu, Consumo Interno, XML NF-e e Relatórios

> Gerado a partir de `docs/prds/prd_matchpoint_v0.6.md`.
> Ordem de criação respeita dependências (blockers primeiro).

---

## Visão geral — grafo de dependências

```
1 Reorganização do menu lateral (frontend)  ─────────────────────────────┐
2 Consumo Interno — model + API (backend)  ──────────────────────────────┤
3 Consumo Interno — telas (frontend)                ── blocked by #2  ──┤
4 XML NF-e — parser + aliases (backend)  ────────────────────────────────┤
5 XML NF-e — modal de importação (frontend)         ── blocked by #4  ──┤
6 Relatórios — hubs por categoria (frontend)        ── blocked by #1  ──┤
7 Relatórios Vendas — novos (full stack)            ── blocked by #6  ──┤
8 Relatórios Compras — novos (full stack)           ── blocked by #6  ──┤
9 Relatórios Financeiro — novos (full stack)        ── blocked by #6  ──┤
10 DRE — linha Consumo Interno (full stack)         ── blocked by #2  ──┘
```

---

## Issue 1 — Reorganização do menu lateral

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Reestruturar o componente `Sidebar.tsx` para agrupar itens em dropdowns lógicos com flyout para o lado direito. Novo agrupamento:

- **Vendas** (ClipboardList): Comandas + Consumo Interno (rota placeholder até issue #3)
- **Estoque** (Package): Estoque + Movimentos (migram de itens flat)
- **Financeiro** (Wallet): Contas a Pagar (migra de item flat)
- **Relatórios** (BarChart3): Vendas, Compras, Financeiro (3 sub-links para hubs)

Remover "Caixa" do menu. "Compras" permanece como link direto (sem dropdown). "Dashboard" e "Cardápio" permanecem como links diretos no topo. "Cadastros" e "Configurações" mantêm padrão atual.

Badges de contagem migram: badge de estoque crítico vai pro grupo Estoque, badge de contas urgentes vai pro grupo Financeiro, badge de comandas abertas vai pro grupo Vendas.

### Critérios de aceite

- [x] Menu exibe grupos: Dashboard, Cardápio, Vendas, Compras, Estoque, Financeiro, Relatórios, Cadastros, Configurações (nesta ordem)
- [x] "Vendas" expande flyout com: Comandas, Consumo Interno
- [x] "Estoque" expande flyout com: Estoque, Movimentos
- [x] "Financeiro" expande flyout com: Contas a Pagar
- [x] "Relatórios" expande flyout com: Vendas, Compras, Financeiro
- [x] "Compras" é dropdown flyout com sub-item Compras (alterado a pedido do cliente)
- [x] "Caixa" não aparece no menu
- [x] Flyout expande para o lado direito em modo expandido e colapsado (via React Portal + fixed positioning)
- [x] Badges migrados para os novos grupos (estoque crítico, contas urgentes, comandas abertas)
- [x] Navegação para todas as rotas existentes continua funcionando
- [x] Não há regressão visual no sidebar em modo desktop e mobile

**Extras implementados (fora do escopo original):**
- [x] Breadcrumb de navegação no topo de todas as telas (ex: "Vendas > Comandas")
- [x] Rota `/comandas` migrada para `/vendas/comandas` para consistência com estrutura do menu
- [x] Nav config extraída para `navConfig.ts` (compartilhada entre Sidebar e Breadcrumb)
- [x] Flyout renderizado via React Portal (resolve clipping de `overflow-y-auto` no nav)

### User stories endereçadas

- US1: Como operador, quero que o menu agrupe itens relacionados em dropdowns.
- US2: Como operador, quero que dropdowns expandam para o lado direito (flyout).
- US3: Como operador, quero que "Caixa" não apareça no menu.
- US4: Como operador, quero que "Compras" seja link direto.

---

## Issue 2 — Consumo Interno: model, migration e API

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Criar o backend completo para o módulo de Consumo Interno.

**Migration:** Criar tabela `itens_consumo_interno` com colunas: `id` (PK), `tenant_id` (FK), `consumidor_id` (FK → users.id), `produto_id` (FK → produtos.id), `quantidade` (Numeric 10,4), `custo_unitario` (Numeric 10,4), `observacao` (Text, nullable), `created_at` (datetime). Adicionar `"saida_consumo_interno"` como tipo válido de `MovimentoEstoque`.

**Model:** `ItemConsumoInterno` com relacionamentos para User e Produto.

**Service:** `consumo_interno_service` com:
- `lancar_item()` — criar registro, calcular `custo_unitario` a partir do `custo_medio` do insumo via ficha técnica, debitar `estoque_atual` imediatamente via `_dar_baixa_estoque_consumo()`, criar `MovimentoEstoque` com tipo `saida_consumo_interno`.
- `estornar_item()` — devolver estoque, criar `MovimentoEstoque` de entrada, deletar registro.
- `listar_items()` — com filtros de consumidor, mês, ano.
- `resumo_mensal()` — agregação por consumidor com totais.

**Endpoints:**
- `POST /api/consumo-interno` — lançar item
- `GET /api/consumo-interno` — listar com filtros
- `GET /api/consumo-interno/resumo` — resumo mensal por consumidor
- `DELETE /api/consumo-interno/{id}` — estornar

**Permissão:** Adicionar `"consumo_interno"` à lista `VALID_SCREENS` em `schemas/profiles.py`.

### Critérios de aceite

- [x] Migration aplicada sem erro — tabela `itens_consumo_interno` criada
- [x] `POST /api/consumo-interno` com `{consumidor_id, produto_id, quantidade}` → item criado com `custo_unitario` calculado pelo `custo_medio` do produto/insumo
- [x] Após lançar item, `estoque_atual` dos insumos da ficha técnica é debitado imediatamente
- [x] Após lançar item, `MovimentoEstoque` criado com `tipo="saida_consumo_interno"`
- [x] `estoque_reservado` NÃO é alterado (diferente da comanda)
- [x] `GET /api/consumo-interno?consumidor_id=1&mes=6&ano=2026` → retorna apenas items do consumidor 1 em junho/2026
- [x] `GET /api/consumo-interno/resumo?mes=6&ano=2026` → retorna `[{consumidor_id, consumidor_nome, itens_no_mes, total, ultima_atividade}]`
- [x] `DELETE /api/consumo-interno/{id}` → estoque devolvido, `MovimentoEstoque` de entrada criado, registro deletado
- [x] Tentar acessar sem permissão `consumo_interno` → 403
- [x] `"consumo_interno"` aparece em `VALID_SCREENS`
- [x] Produto sem ficha técnica → `custo_unitario` é o `custo_medio` do insumo direto (se produto for baseado em insumo) ou `preco_venda` como fallback
- [x] Lançar item não cria registro de pagamento nem impacta contas a pagar/receber

### User stories endereçadas

- US5: registrar consumo sem pagamento
- US6: custo pelo custo médio
- US7: débito imediato no estoque
- US10: filtrar por mês/ano
- US11: permissão `consumo_interno`
- US12: sem impacto financeiro

---

## Issue 3 — Consumo Interno: telas frontend

**Tipo:** AFK
**Bloqueado por:** Issue #2 (API precisa existir)

### O que construir

Criar as telas de Consumo Interno no frontend.

**Visão geral (`ConsumoInternoPage`):**
- Seletor de mês/ano no topo (default: mês atual)
- Tabela com colunas: Consumidor | Itens no mês | Total R$ | Última atividade
- Cada linha é clicável → navega para detalhe
- Totalizador geral no rodapé

**Visão detalhe (`ConsumoInternoDetalhePage`):**
- Nome do consumidor no topo
- Seletor de mês/ano
- Botão "+ Lançar Consumo" → abre modal com: select de produto, input de quantidade, campo de observação
- Tabela com colunas: Item | Qtd | Custo unit. | Subtotal | Data | Ações (estornar)
- Total acumulado em destaque
- Botão de estornar com confirmação

**Rota:** `/consumo-interno` (visão geral), `/consumo-interno/:consumidorId` (detalhe)

**Hook:** `useConsumoInterno()` com queries para listar, resumo, lançar, estornar.

### Critérios de aceite

- [x] Rota `/consumo-interno` acessível via menu Vendas → Consumo Interno
- [x] Visão geral exibe tabela com consumidores e totais do mês selecionado
- [x] Trocar mês/ano atualiza os dados
- [x] Clicar no nome do consumidor navega para detalhe
- [x] Botão "+ Lançar Consumo" abre modal funcional
- [x] Ao lançar item, tabela atualiza e toast de sucesso aparece
- [x] Custo unitário exibido com formatação monetária (R$)
- [x] Total acumulado exibido em destaque
- [x] Botão estornar pede confirmação antes de executar
- [x] Após estorno, item some da tabela e toast confirma
- [x] Sem permissão `consumo_interno`, menu item não aparece e rota redireciona
- [x] Layout responsivo em desktop e mobile

### User stories endereçadas

- US5: registrar consumo sem pagamento
- US8: visão geral com consumidores e totais
- US9: detalhe com itens consumidos
- US10: filtro por mês/ano

---

## Issue 4 — XML NF-e: parser, aliases e API

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Criar o backend para importação de XML de Nota Fiscal Eletrônica.

**Migration:**
- Criar tabela `aliases_insumo_fornecedor` com: `id` (PK), `tenant_id`, `fornecedor_id` (FK), `nome_nota` (VARCHAR 300), `ean` (VARCHAR 20, nullable), `insumo_id` (FK), `created_at`. Unique constraint em `(tenant_id, fornecedor_id, nome_nota)`.
- Adicionar coluna `ean` (VARCHAR 20, nullable) à tabela `insumos`.

**Parser (`xml_nfe_parser.py`):**
- Parsear XML com `xml.etree.ElementTree`, namespace `http://www.portalfiscal.inf.br/nfe`
- Extrair: dados do emitente (CNPJ, razão social), número da nota, data de emissão
- Extrair itens: código do produto, EAN/GTIN, descrição, quantidade, unidade, valor unitário, valor total
- Retornar estrutura tipada com todos os campos

**Matcher (`xml_nfe_matcher.py`):**
- Para cada item, buscar match: 1º por EAN no `insumos.ean`, 2º por EAN nos aliases, 3º por `nome_nota` + `fornecedor_id` nos aliases
- Retornar lista de itens com status: `matched` (com `insumo_id`) ou `pending`

**Endpoints:**
- `POST /api/compras/importar-xml` — upload multipart, retorna `{fornecedor: {cnpj, nome}, numero_nota, data_emissao, items: [{nome, ean, quantidade, unidade, custo_unitario, total, insumo_id?, status}]}`
- `POST /api/compras/confirmar-importacao` — recebe itens validados + aliases novos, cria compra automaticamente, salva aliases para matches futuros

**Schema de insumo:** Incluir `ean` no response e no create/update.

### Critérios de aceite

- [ ] Migration aplicada sem erro — tabela `aliases_insumo_fornecedor` criada, coluna `ean` adicionada a `insumos`
- [ ] `POST /api/compras/importar-xml` com XML válido da SEFAZ → retorna itens parseados corretamente
- [ ] XML com namespace NF-e 4.00 é parseado corretamente
- [ ] XML inválido ou corrompido → retorna erro 400 com mensagem clara
- [ ] Item com EAN correspondente a `insumos.ean` → status `matched` com `insumo_id`
- [ ] Item com alias existente (fornecedor + nome) → status `matched`
- [ ] Item sem match → status `pending`, `insumo_id` = null
- [ ] `POST /api/compras/confirmar-importacao` → compra criada com todos os itens, aliases salvos
- [ ] Na segunda importação do mesmo fornecedor, items previamente associados são automaticamente matched
- [ ] `GET /api/insumos` inclui campo `ean` no response
- [ ] Editar insumo permite definir `ean`

### User stories endereçadas

- US15: upload XML e extração automática
- US17: match automático por EAN
- US18: aliases lembram associações
- US20: confirmar e gerar compra
- US22: compra manual continua funcionando

---

## Issue 5 — XML NF-e: modal de importação no frontend

**Tipo:** AFK
**Bloqueado por:** Issue #4 (API precisa existir)

### O que construir

Criar o modal de importação de XML na tela de Compras.

**Botão trigger:** "Importar XML" com ícone `FileUp`, posicionado à esquerda de "+ Nova Compra" no header de `ComprasPage`.

**Modal `ImportarXmlModal` — 3 steps:**

**Step 1 — Upload:**
- Área de drag-and-drop ou input file para .xml
- Validação de extensão (.xml)
- Ao selecionar, chama `POST /api/compras/importar-xml`
- Loading spinner durante parsing

**Step 2 — Validação:**
- Cabeçalho: nome do fornecedor (da nota), número da nota, data de emissão
- Se fornecedor não está cadastrado: aviso + botão para cadastrar inline
- Lista de itens em duas colunas:
  - Esquerda: nome do item na nota, EAN, quantidade, valor
  - Direita: dropdown de insumos cadastrados (com busca), ou botão "+ Criar insumo"
- Indicador visual: verde = match automático, amarelo = pendente
- Contador: "X de Y itens associados"
- Botão "Confirmar tudo" habilitado só quando todos os itens estão associados

**Step 3 — Confirmação:**
- Resumo: fornecedor, número da nota, quantidade de itens, valor total
- Botão "Gerar Compra" → chama `POST /api/compras/confirmar-importacao`
- Sucesso → fecha modal, navega para a compra criada

**Ícone de ajuda (?):** Popover no canto inferior com passo a passo para baixar XML do portal SEFAZ. Possivelmente link para o portal.

### Critérios de aceite

- [ ] Botão "Importar XML" visível na tela de Compras, ao lado de "+ Nova Compra"
- [ ] Clicar abre modal com área de upload
- [ ] Arrastar/selecionar arquivo .xml → sistema parseia e mostra itens
- [ ] Arquivo não-XML → mensagem de erro "Arquivo inválido"
- [ ] Itens com match automático exibem badge verde e insumo pré-selecionado
- [ ] Itens sem match exibem badge amarelo e dropdown vazio
- [ ] Alterar insumo no dropdown atualiza o status de amarelo para verde
- [ ] Criar insumo inline → novo insumo aparece no dropdown e fica selecionado
- [ ] "Confirmar tudo" desabilitado enquanto houver itens pendentes
- [ ] Após confirmação, compra é criada e modal fecha
- [ ] Toast de sucesso: "Compra importada com sucesso"
- [ ] Ícone "?" exibe popover com instruções do SEFAZ
- [ ] Segunda importação do mesmo fornecedor: itens previamente associados aparecem verdes automaticamente

### User stories endereçadas

- US14: botão "Importar XML" na tela de Compras
- US15: upload e extração automática
- US16: tela de validação visual com associação
- US17: match automático (verde) e pendente (amarelo)
- US19: criar insumo novo na tela de validação
- US20: "Confirmar tudo" gera compra
- US21: ícone de ajuda com passo a passo SEFAZ

---

## Issue 6 — Relatórios: hubs por categoria + migração de rotas

**Tipo:** AFK
**Bloqueado por:** Issue #1 (menu precisa ter 3 sub-links de relatórios)

### O que construir

Substituir a página única de relatórios (`RelatoriosIndexPage`) por 3 páginas hub separadas:

**`RelatoriosVendasHubPage` (`/relatorios/vendas`):**
Cards para 12 relatórios: Vendas do Dia, Histórico Comandas, Fechamento Caixa, Vendas por Garçom, Produtos Mais Vendidos, Pico Vendas Horário, Vendas por Produto, Consumo Interno (novo), Ticket Médio (novo), Vendas por Categoria (novo), Vendas por Método Pgto (novo), Comparativo de Períodos (novo). Cards de relatórios novos ficam com badge "Em breve" até serem implementados.

**`RelatoriosComprasHubPage` (`/relatorios/compras`):**
Cards para 6 relatórios: Histórico de Compras, Gastos por Fornecedor, Evolução de Preços, Compras por Categoria, Compras por Período, Contas Vencidas/A Vencer. Todos com badge "Em breve" até implementação.

**`RelatoriosFinanceiroHubPage` (`/relatorios/financeiro`):**
Cards para 6 relatórios: DRE, CMV por Produto, Perdas e Cortesias (existentes — mover), Fluxo de Caixa (novo), Margem por Categoria (novo), Resumo Financeiro Mensal (novo). Novos com badge "Em breve".

**Migração de rotas:**
- Relatórios existentes ganham novas rotas com prefixo de categoria (`/relatorios/vendas/vendas-do-dia`, etc.)
- Rotas antigas redirecionam para novas (React Router `<Navigate>`)
- Rota `/relatorios` redireciona para `/relatorios/vendas` (hub padrão)

**Layout dos hubs:** Grid responsivo (3 colunas lg, 2 sm, 1 mobile) com cards clicáveis. Cada card: ícone, título, descrição curta. Padrão visual da `RelatoriosIndexPage` atual.

### Critérios de aceite

- [ ] Menu → Relatórios → Vendas navega para `/relatorios/vendas`
- [ ] Menu → Relatórios → Compras navega para `/relatorios/compras`
- [ ] Menu → Relatórios → Financeiro navega para `/relatorios/financeiro`
- [ ] Hub Vendas exibe 12 cards (7 existentes + 5 "Em breve")
- [ ] Hub Compras exibe 6 cards (todos "Em breve")
- [ ] Hub Financeiro exibe 6 cards (3 existentes + 3 "Em breve")
- [ ] Cards de relatórios existentes navegam para a página correta
- [ ] Cards "Em breve" são clicáveis mas exibem toast "Relatório em desenvolvimento"
- [ ] Rota antiga `/relatorios/vendas-do-dia` redireciona para `/relatorios/vendas/vendas-do-dia`
- [ ] Rota `/relatorios` redireciona para `/relatorios/vendas`
- [ ] Layout responsivo: 3 colunas em desktop, 2 em tablet, 1 em mobile
- [ ] Nenhum relatório existente perde acesso ou funcionalidade

### User stories endereçadas

- US23: dropdown no menu com 3 sublinks
- US24: cada sublink abre hub com cards

---

## Issue 7 — Relatórios Vendas: 5 novos endpoints e páginas

**Tipo:** HITL
**Bloqueado por:** Issue #6 (hubs precisam existir), Issue #2 (consumo interno para relatório de consumo)

### O que construir

Implementar 5 novos relatórios de vendas, cada um com endpoint backend + página frontend:

**7a. Consumo Interno** (`/relatorios/vendas/consumo-interno`)
- Backend: `GET /api/relatorios/vendas/consumo-interno?mes=&ano=` → dados agregados por consumidor
- Frontend: tabela com consumidor, itens, total. Filtro de período. Gráfico pizza de distribuição.

**7b. Ticket Médio por Período** (`/relatorios/vendas/ticket-medio`)
- Backend: `GET /api/relatorios/vendas/ticket-medio?de=&ate=&agrupamento=dia|semana|mes` → série temporal
- Frontend: gráfico de linha mostrando evolução do ticket médio. Filtros de data e agrupamento.

**7c. Vendas por Categoria** (`/relatorios/vendas/vendas-por-categoria`)
- Backend: `GET /api/relatorios/vendas/por-categoria?de=&ate=` → faturamento por categoria
- Frontend: gráfico de barras horizontais + tabela. Filtro de data.

**7d. Vendas por Método de Pagamento** (`/relatorios/vendas/vendas-por-metodo-pagamento`)
- Backend: `GET /api/relatorios/vendas/por-metodo-pagamento?de=&ate=` → distribuição por método
- Frontend: gráfico pizza + tabela com valores e percentuais. Filtro de data.

**7e. Comparativo de Períodos** (`/relatorios/vendas/comparativo-periodos`)
- Backend: `GET /api/relatorios/vendas/comparativo?periodo_atual_de=&periodo_atual_ate=&periodo_anterior_de=&periodo_anterior_ate=` → métricas de ambos períodos com variação %
- Frontend: cards lado a lado (período atual vs anterior) com setas de variação (verde ↑, vermelho ↓). Métricas: faturamento, nº comandas, ticket médio, itens vendidos.

### Critérios de aceite

- [ ] Todos os 5 endpoints retornam dados corretos com filtros aplicados
- [ ] Todas as 5 páginas renderizam corretamente com dados e sem dados
- [ ] Relatório de Consumo Interno: dados agregados por consumidor batem com registros de `itens_consumo_interno`
- [ ] Ticket Médio: cálculo correto (faturamento total / nº comandas no período)
- [ ] Vendas por Categoria: soma de faturamento por categoria bate com total geral
- [ ] Vendas por Método Pgto: percentuais somam 100%
- [ ] Comparativo: variação % calculada corretamente, seta verde quando positiva, vermelha quando negativa
- [ ] Cards "Em breve" nos hubs são substituídos por links funcionais
- [ ] Filtros de data funcionam corretamente
- [ ] Layout responsivo em todas as páginas

### User stories endereçadas

- US25: relatório de Consumo Interno
- US26: Ticket Médio por Período
- US27: Vendas por Categoria
- US28: Vendas por Método de Pagamento
- US29: Comparativo de Períodos

---

## Issue 8 — Relatórios Compras: 6 novos endpoints e páginas

**Tipo:** HITL
**Bloqueado por:** Issue #6 (hubs precisam existir)

### O que construir

Implementar 6 novos relatórios de compras, cada um com endpoint backend + página frontend:

**8a. Histórico de Compras** (`/relatorios/compras/historico`)
- Backend: `GET /api/relatorios/compras/historico?de=&ate=&fornecedor_id=&status=` → lista paginada
- Frontend: tabela com data, fornecedor, nº nota, itens, total, status. Filtros de data, fornecedor, status.

**8b. Gastos por Fornecedor** (`/relatorios/compras/gastos-por-fornecedor`)
- Backend: `GET /api/relatorios/compras/gastos-por-fornecedor?de=&ate=` → ranking com totais
- Frontend: tabela ranking + gráfico barras. Filtro de data.

**8c. Evolução de Preços de Insumos** (`/relatorios/compras/evolucao-precos`)
- Backend: `GET /api/relatorios/compras/evolucao-precos?insumo_ids=&de=&ate=` → série temporal por insumo
- Frontend: gráfico de linha com seletor de insumos (multiselect). Filtro de data.

**8d. Compras por Categoria** (`/relatorios/compras/compras-por-categoria`)
- Backend: `GET /api/relatorios/compras/por-categoria?de=&ate=` → gasto por categoria de insumo
- Frontend: gráfico pizza + tabela. Filtro de data.

**8e. Compras por Período** (`/relatorios/compras/compras-por-periodo`)
- Backend: `GET /api/relatorios/compras/por-periodo?de=&ate=&agrupamento=semana|mes` → série temporal
- Frontend: gráfico de barras com volume/valor por período. Filtro de data e agrupamento.

**8f. Contas Vencidas/A Vencer** (`/relatorios/compras/contas-vencidas`)
- Backend: `GET /api/relatorios/compras/contas-vencidas` → compras com `data_vencimento` passada ou próxima
- Frontend: duas seções: "Vencidas" (vermelho) e "A vencer nos próximos 7/15/30 dias" (amarelo). Tabela com fornecedor, valor, dias de atraso/até vencimento.

### Critérios de aceite

- [ ] Todos os 6 endpoints retornam dados corretos
- [ ] Histórico de Compras: paginação funciona, filtros aplicam corretamente
- [ ] Gastos por Fornecedor: ranking ordenado por valor total descrescente
- [ ] Evolução de Preços: gráfico mostra linha por insumo selecionado
- [ ] Compras por Categoria: agrupa por categoria do insumo (não do produto)
- [ ] Compras por Período: agrupamento semana/mês funciona
- [ ] Contas Vencidas: separa corretamente vencidas vs a vencer
- [ ] Todas as páginas renderizam corretamente com dados e sem dados (empty state)
- [ ] Cards "Em breve" no hub Compras substituídos por links funcionais

### User stories endereçadas

- US30: Histórico de Compras
- US31: Gastos por Fornecedor
- US32: Evolução de Preços
- US33: Compras por Categoria
- US34: Compras por Período
- US35: Contas Vencidas/A Vencer

---

## Issue 9 — Relatórios Financeiro: 3 novos endpoints e páginas

**Tipo:** HITL
**Bloqueado por:** Issue #6 (hubs precisam existir)

### O que construir

Implementar 3 novos relatórios financeiros, cada um com endpoint backend + página frontend:

**9a. Fluxo de Caixa** (`/relatorios/financeiro/fluxo-de-caixa`)
- Backend: `GET /api/relatorios/financeiro/fluxo-de-caixa?de=&ate=&agrupamento=dia|semana|mes` → entradas (vendas) e saídas (compras, contas a pagar) por período
- Frontend: gráfico de barras empilhadas (entradas vs saídas) + linha de saldo acumulado. Tabela detalhada abaixo. Filtros de data e agrupamento.

**9b. Margem por Categoria** (`/relatorios/financeiro/margem-por-categoria`)
- Backend: `GET /api/relatorios/financeiro/margem-por-categoria?de=&ate=` → para cada categoria: receita, custo (via CMV), margem bruta, margem %
- Frontend: tabela com colunas: Categoria | Receita | Custo | Margem R$ | Margem % + gráfico de barras comparativo. Filtro de data.

**9c. Resumo Financeiro Mensal** (`/relatorios/financeiro/resumo-mensal`)
- Backend: `GET /api/relatorios/financeiro/resumo-mensal?mes=&ano=` → consolidado: receita total, custo total (CMV + consumo interno), margem bruta, nº comandas, ticket médio, top 5 produtos, top 3 fornecedores
- Frontend: dashboard com cards de KPI no topo + seções de detalhe abaixo. Seletor de mês/ano.

### Critérios de aceite

- [ ] Todos os 3 endpoints retornam dados corretos
- [ ] Fluxo de Caixa: entradas = soma de pagamentos recebidos, saídas = soma de compras + contas a pagar
- [ ] Fluxo de Caixa: saldo acumulado calculado corretamente
- [ ] Margem por Categoria: margem % = (receita - custo) / receita × 100
- [ ] Margem por Categoria: custo calculado via ficha técnica (CMV real)
- [ ] Resumo Mensal: consolidado bate com soma dos outros relatórios
- [ ] Resumo Mensal: consumo interno aparece separado do CMV de vendas
- [ ] Todas as páginas renderizam com dados e sem dados
- [ ] Cards "Em breve" no hub Financeiro substituídos por links funcionais

### User stories endereçadas

- US36: Fluxo de Caixa
- US37: Margem por Categoria
- US38: Resumo Financeiro Mensal

---

## Issue 10 — DRE: adicionar linha Consumo Interno

**Tipo:** AFK
**Bloqueado por:** Issue #2 (tabela `itens_consumo_interno` precisa existir)

### O que construir

Atualizar o relatório DRE existente para incluir linha de Consumo Interno.

**Backend:** No endpoint de DRE existente, adicionar query à tabela `itens_consumo_interno` para calcular total de consumo interno no período. Incluir como nova linha na resposta, na seção de custos/deduções.

**Frontend:** Exibir linha "Consumo Interno" no DRE entre as linhas de custo. Valor em negativo (é custo, não receita). NÃO somar com vendas — é linha separada.

**Posição na DRE:**
```
Receita Bruta
  (-) Cortesias
  = Receita Líquida
  (-) CMV
  (-) Consumo Interno    ← NOVA LINHA
  = Lucro Bruto
```

### Critérios de aceite

- [ ] Endpoint de DRE inclui campo `consumo_interno` no response
- [ ] Valor de consumo interno calculado corretamente a partir de `itens_consumo_interno` no período
- [ ] DRE no frontend exibe linha "Consumo Interno" com valor formatado
- [ ] Consumo Interno é subtraído para calcular Lucro Bruto
- [ ] Se não houver consumo interno no período, linha exibe R$ 0,00
- [ ] Não há regressão nos demais valores da DRE

### User stories endereçadas

- US13: consumo interno como linha separada no DRE

---

## Resumo

| # | Título | Tipo | Bloqueado por | Status |
|---|--------|------|--------------|--------|
| 1 | Reorganização do menu lateral | AFK | — | ✅ |
| 2 | Consumo Interno — model + API | AFK | — | ✅ |
| 3 | Consumo Interno — telas frontend | AFK | #2 | ✅ |
| 4 | XML NF-e — parser + aliases + API | AFK | — | ⬜ |
| 5 | XML NF-e — modal de importação | AFK | #4 | ⬜ |
| 6 | Relatórios — hubs por categoria | AFK | #1 | ⬜ |
| 7 | Relatórios Vendas — 5 novos | HITL | #6, #2 | ⬜ |
| 8 | Relatórios Compras — 6 novos | HITL | #6 | ⬜ |
| 9 | Relatórios Financeiro — 3 novos | HITL | #6 | ⬜ |
| 10 | DRE — linha Consumo Interno | AFK | #2 | ⬜ |

**Início paralelo possível:** Issues 1, 2, 4 podem iniciar simultaneamente (sem dependências entre si).

**Caminho crítico:** #1 → #6 → #7/#8/#9 (menu → hubs → relatórios novos).

**10 issues, 3 concluídas.**
