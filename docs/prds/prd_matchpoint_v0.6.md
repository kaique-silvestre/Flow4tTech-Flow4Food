# PRD Matchpoint v0.6 — Menu Lateral, Consumo Interno, XML NF-e e Relatórios

**Data:** 2026-06-04
**Status:** Aprovado para implementação

---

## Problem Statement

O sistema Matchpoint está em operação no estabelecimento Estação Backpoint, mas enfrenta limitações que dificultam o controle operacional completo:

1. **Menu lateral desorganizado** — itens como Estoque, Movimentos, Contas a Pagar e Relatórios estão em nível flat, sem agrupamento lógico. Com o crescimento do sistema, a navegação ficou poluída e difícil de escanear. Caixa aparece no menu mas não será implementado agora.

2. **Sem controle de consumo interno** — os 3 sócios (Matheus, Guerreiro, Denise) consomem produtos do próprio estabelecimento e não têm forma de rastrear isso. Hoje consomem sem registro, o que gera divergência no estoque e impossibilita saber quanto cada sócio consumiu por mês. Precisam de um fluxo simplificado (sem pagamento, sem caixa) que debite estoque imediatamente pelo custo médio.

3. **Cadastro manual de compras é lento e propenso a erros** — o operador digita manualmente todos os itens de cada nota fiscal de compra. A importação de XML da NF-e (disponível no portal SEFAZ) eliminaria redigitação, mas precisa ser extremamente simples — se for complicado, o cliente volta pro papel.

4. **Relatórios insuficientes e mal organizados** — existem 10 relatórios numa página única. Faltam relatórios de compras (nenhum existe), relatórios financeiros avançados (fluxo de caixa, margem por categoria) e relatórios de vendas analíticos (ticket médio, comparativo de períodos). A página única não escala para 24 relatórios.

---

## Solution

Quatro frentes de trabalho que expandem significativamente as capacidades do sistema:

1. **Reorganizar menu lateral** — agrupar itens em dropdowns lógicos (Vendas, Estoque, Financeiro, Relatórios) com flyout para o lado direito. Remover Caixa. Máximo 2 níveis de profundidade.

2. **Criar módulo de Consumo Interno** — nova tela em Vendas → Consumo Interno com fluxo simplificado: selecionar consumidor, adicionar itens (débito imediato no estoque pelo custo médio), visualizar acumulado mensal por pessoa. Sem pagamento, sem caixa, sem lucro.

3. **Importar XML NF-e nas compras** — botão "Importar XML" na tela de Compras abre modal com upload, parsing automático, tela de validação visual com match por EAN/aliases, e geração automática da compra. Match inteligente sem IA, sem custo.

4. **Reorganizar e expandir relatórios** — dividir em 3 hubs (Vendas, Compras, Financeiro) acessíveis via dropdown no menu. Adicionar 14 novos relatórios. Atualizar DRE com linha de Consumo Interno.

---

## User Stories

### Menu Lateral

1. Como operador, quero que o menu agrupe itens relacionados em dropdowns (Vendas, Estoque, Financeiro, Relatórios), para encontrar funcionalidades mais rápido.
2. Como operador, quero que dropdowns expandam para o lado direito (flyout) quando o sidebar está expandido, mantendo o padrão visual já existente em Cadastros/Configurações.
3. Como operador, quero que "Caixa" não apareça no menu, para não gerar confusão com funcionalidade inexistente.
4. Como operador, quero que "Compras" seja um link direto (sem dropdown), pois só tem uma página.

### Consumo Interno

5. Como sócio, quero registrar itens que consumi do estabelecimento sem passar por fluxo de pagamento, para manter controle sem burocracia.
6. Como sócio, quero que o valor do consumo seja calculado pelo custo médio do insumo (preço de custo), não pelo preço de venda, pois não é uma venda.
7. Como sócio, quero que o estoque seja debitado imediatamente ao lançar um item de consumo, para que o controle de estoque reflita a realidade em tempo real.
8. Como sócio, quero ver uma visão geral com todos os consumidores e seus totais mensais (itens no mês, total R$, última atividade), para comparar consumo.
9. Como sócio, quero clicar no meu nome e ver o detalhe dos itens consumidos (item, quantidade, custo unitário, subtotal) com total acumulado, para entender o que consumi.
10. Como sócio, quero filtrar por mês/ano para ver consumo de períodos anteriores, sem conceito de "fechamento" de mês.
11. Como admin, quero controlar quem pode acessar Consumo Interno via permissão `consumo_interno` na gestão de usuários.
12. Como gerente, quero que consumo interno NÃO impacte o caixa/fluxo financeiro — é só registro de controle.
13. Como gerente, quero ver consumo interno como linha separada no DRE, para não misturar com vendas.

### Importação XML NF-e

14. Como operador, quero ver um botão "Importar XML" ao lado de "+ Nova Compra" na tela de Compras, para acessar a importação facilmente.
15. Como operador, quero fazer upload de um arquivo .xml de nota fiscal eletrônica e ver os itens extraídos automaticamente, para não precisar digitar manualmente.
16. Como operador, quero ver uma tela de validação com o item da nota à esquerda e dropdown de insumos cadastrados à direita, para associar cada item da nota a um insumo do sistema.
17. Como operador, quero que itens com código EAN/GTIN correspondente sejam associados automaticamente (verde), e itens sem match fiquem pendentes (amarelo), para acelerar o processo.
18. Como operador, quero que o sistema lembre a associação entre nome na nota + fornecedor → insumo (aliases), para que na próxima importação do mesmo fornecedor os matches sejam automáticos.
19. Como operador, quero poder criar um insumo novo diretamente na tela de validação quando o item da nota não corresponde a nenhum insumo existente.
20. Como operador, quero clicar "Confirmar tudo" e ter a compra gerada automaticamente com todos os itens validados.
21. Como operador, quero ver um ícone "?" com passo a passo de como baixar o XML do portal SEFAZ, pois ainda não tenho esse hábito.
22. Como operador, quero continuar usando cadastro manual de compras normalmente — XML é opcional.

### Relatórios — Organização

23. Como gerente, quero acessar relatórios via dropdown no menu com 3 sublinks (Vendas, Compras, Financeiro), para ir direto à categoria desejada.
24. Como gerente, quero que cada sublink abra uma página hub com cards dos relatórios disponíveis, para visualizar todas as opções de uma vez.

### Relatórios — Vendas (novos)

25. Como gerente, quero ver relatório de Consumo Interno com total por consumidor e período, para controlar gastos dos sócios.
26. Como gerente, quero ver relatório de Ticket Médio por Período com gráfico de evolução ao longo do tempo, para identificar tendências.
27. Como gerente, quero ver relatório de Vendas por Categoria do cardápio, para saber quais categorias geram mais faturamento.
28. Como gerente, quero ver relatório de Vendas por Método de Pagamento, para saber quanto entra em dinheiro, cartão, pix, etc.
29. Como gerente, quero ver relatório Comparativo de Períodos (semana/mês atual vs anterior), para avaliar crescimento ou queda.

### Relatórios — Compras (todos novos)

30. Como gerente, quero ver Histórico de Compras com filtros de data e fornecedor, para auditar compras passadas.
31. Como gerente, quero ver Gastos por Fornecedor com ranking e totais, para negociar melhor.
32. Como gerente, quero ver Evolução de Preços de Insumos ao longo do tempo, para detectar aumentos abusivos.
33. Como gerente, quero ver Compras por Categoria de insumo, para saber onde gasto mais.
34. Como gerente, quero ver Compras por Período (mensal/semanal), para entender sazonalidade.
35. Como gerente, quero ver Contas Vencidas/A Vencer, para controlar inadimplência com fornecedores.

### Relatórios — Financeiro (novos)

36. Como gerente, quero ver Fluxo de Caixa (entradas vs saídas por período), para entender a saúde financeira.
37. Como gerente, quero ver Margem por Categoria, para saber quais categorias são mais lucrativas.
38. Como gerente, quero ver Resumo Financeiro Mensal consolidado (receita, custo, margem, consumo interno), para ter visão geral do mês.

---

## Implementation Decisions

### 1. Menu Lateral

**Estrutura final do menu:**
```
Dashboard           (LayoutDashboard)
Cardápio            (UtensilsCrossed)
▶ Vendas            (ClipboardList)
    Comandas
    Consumo Interno          ← NOVO
Compras             (ShoppingCart)       ← link direto
▶ Estoque           (Package)
    Estoque
    Movimentos
▶ Financeiro        (Wallet)
    Contas a Pagar
▶ Relatórios        (BarChart3)
    Vendas
    Compras
    Financeiro
▶ Cadastros         (BookOpen)          ← já existe
▶ Configurações     (Settings)          ← já existe
```

**Módulos a modificar:**
- `frontend/src/components/layout/Sidebar.tsx` — reestruturar array de menu items, agrupar Comandas+Consumo Interno em "Vendas", Estoque+Movimentos em "Estoque", Contas a Pagar em "Financeiro", Relatórios em 3 sub-links. Remover "Caixa".
- `frontend/src/App.tsx` — adicionar rotas para novas páginas de relatórios e consumo interno.

**Regras:**
- Flyout para o lado direito em todos os dropdowns (padrão já existe no collapsed mode — expandir para modo aberto)
- Compras NÃO é dropdown — link direto
- Máximo 2 níveis de profundidade
- Badges de contagem migram para os novos grupos (estoque crítico → grupo Estoque, contas urgentes → grupo Financeiro)

### 2. Consumo Interno

**Novo model:**
```python
class ItemConsumoInterno(Base):
    __tablename__ = "itens_consumo_interno"

    id: int (PK)
    tenant_id: int (FK)
    consumidor_id: int (FK → users.id)
    produto_id: int (FK → produtos.id)
    quantidade: Decimal(10, 4)
    custo_unitario: Decimal(10, 4)   # snapshot do custo_medio no momento
    observacao: Optional[str]
    created_at: datetime
```

**Decisões:**
- Sem model pai (sessão/comanda). Cada item é um registro independente. Agrupamento é feito por query (consumidor + mês).
- `custo_unitario` é snapshot do `custo_medio` do insumo no momento do lançamento — não muda se o custo médio for recalculado depois.
- Débito imediato no estoque: ao lançar item, chamar `_dar_baixa_estoque_consumo()` que debita `estoque_atual` e cria `MovimentoEstoque` com `tipo="saida_consumo_interno"`.
- SEM reserva de estoque (diferente da comanda normal). Débito é direto e imediato.
- SEM impacto financeiro — não cria registros em contas a pagar/receber nem altera caixa.
- Permissão `consumo_interno` adicionada a `VALID_SCREENS`.

**Endpoints:**
- `POST /api/consumo-interno` — lançar item (body: `consumidor_id`, `produto_id`, `quantidade`, `observacao?`)
- `GET /api/consumo-interno` — listar items com filtros (`consumidor_id?`, `mes?`, `ano?`)
- `GET /api/consumo-interno/resumo` — visão agregada por consumidor no mês (`consumidor`, `itens_no_mes`, `total`, `ultima_atividade`)
- `DELETE /api/consumo-interno/{id}` — estornar item (devolve estoque, remove registro)

**Telas:**
- `ConsumoInternoPage` — visão geral: tabela com consumidores, filtro de mês/ano, totais
- `ConsumoInternoDetalhePage` — detalhe: itens de um consumidor no período, com lançamento inline

**Migration:** 1 nova tabela `itens_consumo_interno`. Adicionar `"saida_consumo_interno"` ao enum de tipos de movimento.

### 3. Importação XML NF-e

**Novo model:**
```python
class AliasInsumoFornecedor(Base):
    __tablename__ = "aliases_insumo_fornecedor"

    id: int (PK)
    tenant_id: int
    fornecedor_id: int (FK → fornecedores.id)
    nome_nota: str          # nome do produto como aparece na NF-e
    ean: Optional[str]      # código EAN/GTIN da nota
    insumo_id: int (FK → insumos.id)
    created_at: datetime

    # Unique constraint: (tenant_id, fornecedor_id, nome_nota)
```

**Parser XML:**
- Extrair dados da tag `<emit>` (fornecedor: CNPJ, nome)
- Extrair itens de `<det>/<prod>` (cProd, cEAN, xProd, qCom, uCom, vUnCom, vProd)
- Extrair dados de `<ide>` (nNF = número da nota, dhEmi = data de emissão)
- Biblioteca: `xml.etree.ElementTree` (stdlib, sem dependência extra)
- Namespace NF-e: `http://www.portalfiscal.inf.br/nfe`

**Fluxo de match:**
1. Para cada item da nota, buscar match por EAN: `SELECT insumo_id FROM aliases WHERE ean = ? AND fornecedor_id = ?`
2. Se não encontrou por EAN, buscar por nome: `SELECT insumo_id FROM aliases WHERE nome_nota = ? AND fornecedor_id = ?`
3. Se encontrou → status "matched" (verde). Se não → status "pending" (amarelo).
4. Ao confirmar match manual, criar/atualizar registro em `aliases_insumo_fornecedor`.

**Endpoints:**
- `POST /api/compras/importar-xml` — recebe arquivo XML, retorna itens parseados com status de match
- `POST /api/compras/confirmar-importacao` — recebe itens validados, cria compra + atualiza aliases

**Frontend:**
- `ImportarXmlModal` — modal com 3 steps: upload → validação → confirmação
- Dentro de `ComprasPage`, botão "Importar XML" à esquerda de "+ Nova Compra"
- Ícone "?" com tooltip/popover explicando como baixar XML do SEFAZ

**Migration:** 1 nova tabela `aliases_insumo_fornecedor`. Adicionar campo `ean` (VARCHAR, nullable) à tabela `insumos`.

### 4. Relatórios

**Reestruturação de rotas:**
```
/relatorios/vendas           → Hub Vendas (12 cards)
/relatorios/compras          → Hub Compras (6 cards)
/relatorios/financeiro       → Hub Financeiro (6 cards)
/relatorios/vendas/...       → Páginas individuais
/relatorios/compras/...      → Páginas individuais
/relatorios/financeiro/...   → Páginas individuais
```

**Relatórios existentes — redistribuição:**

| Relatório | Rota atual | Nova rota |
|-----------|-----------|-----------|
| Vendas do Dia | `/relatorios/vendas-do-dia` | `/relatorios/vendas/vendas-do-dia` |
| Histórico Comandas | `/relatorios/historico` | `/relatorios/vendas/historico` |
| Fechamento Caixa | `/relatorios/fechamento-caixa` | `/relatorios/vendas/fechamento-caixa` |
| Vendas por Garçom | `/relatorios/vendas-por-garcom` | `/relatorios/vendas/vendas-por-garcom` |
| Produtos Mais Vendidos | `/relatorios/produtos-mais-vendidos` | `/relatorios/vendas/produtos-mais-vendidos` |
| Pico Vendas Horário | `/relatorios/pico-vendas-horario` | `/relatorios/vendas/pico-vendas-horario` |
| Vendas por Produto | `/relatorios/vendas-por-produto` | `/relatorios/vendas/vendas-por-produto` |
| DRE | `/relatorios/dre` | `/relatorios/financeiro/dre` |
| CMV por Produto | `/relatorios/cmv` | `/relatorios/financeiro/cmv` |
| Perdas e Cortesias | `/relatorios/perdas-cortesias` | `/relatorios/financeiro/perdas-cortesias` |

**Novos relatórios — Vendas (5):**

| Relatório | Rota | Dados principais |
|-----------|------|-----------------|
| Consumo Interno | `/relatorios/vendas/consumo-interno` | Total por consumidor, período, itens |
| Ticket Médio por Período | `/relatorios/vendas/ticket-medio` | Gráfico de evolução temporal do ticket médio |
| Vendas por Categoria | `/relatorios/vendas/vendas-por-categoria` | Faturamento agrupado por categoria do cardápio |
| Vendas por Método Pgto | `/relatorios/vendas/vendas-por-metodo-pagamento` | Distribuição de receita por método (dinheiro, cartão, pix) |
| Comparativo de Períodos | `/relatorios/vendas/comparativo-periodos` | Semana/mês atual vs anterior com variação % |

**Novos relatórios — Compras (6):**

| Relatório | Rota | Dados principais |
|-----------|------|-----------------|
| Histórico de Compras | `/relatorios/compras/historico` | Lista de compras com filtros de data/fornecedor |
| Gastos por Fornecedor | `/relatorios/compras/gastos-por-fornecedor` | Ranking de fornecedores por valor total |
| Evolução de Preços | `/relatorios/compras/evolucao-precos` | Gráfico de preço de insumos ao longo do tempo |
| Compras por Categoria | `/relatorios/compras/compras-por-categoria` | Gasto agrupado por categoria de insumo |
| Compras por Período | `/relatorios/compras/compras-por-periodo` | Volume mensal/semanal de compras |
| Contas Vencidas/A Vencer | `/relatorios/compras/contas-vencidas` | Visão de inadimplência com fornecedores |

**Novos relatórios — Financeiro (3):**

| Relatório | Rota | Dados principais |
|-----------|------|-----------------|
| Fluxo de Caixa | `/relatorios/financeiro/fluxo-de-caixa` | Entradas vs saídas por período |
| Margem por Categoria | `/relatorios/financeiro/margem-por-categoria` | Margem de lucro por categoria do cardápio |
| Resumo Financeiro Mensal | `/relatorios/financeiro/resumo-mensal` | Consolidado: receita, custo, margem, consumo interno |

**DRE — atualização:**
- Adicionar linha "Consumo Interno" na seção de custos, calculada a partir da tabela `itens_consumo_interno`
- Não mistura com receita de vendas

### Decisões arquiteturais gerais

- **Consumo Interno: sem model de sessão** — items são registros soltos, agrupamento por query. Simplifica CRUD e evita complexidade de "abrir/fechar consumo".
- **Consumo Interno: débito imediato** — sem reserva. Diferente da comanda, não há "aberto aguardando fechamento".
- **Consumo Interno: custo_medio snapshot** — valor gravado no momento do lançamento. Se custo_medio do insumo mudar depois, registros anteriores mantêm o valor original.
- **XML: match por EAN primeiro, depois por nome+fornecedor** — prioriza match exato. Aliases aprendem com uso.
- **XML: popup, não página separada** — mantém contexto da tela de compras. 3 steps no modal.
- **Relatórios: 3 hubs, não 1** — escala melhor com 24 relatórios. Cada hub é uma página com grid de cards.
- **Rotas de relatórios: prefixo por categoria** — `/relatorios/vendas/...`, `/relatorios/compras/...`, `/relatorios/financeiro/...`. Rotas antigas redirecionam para novas (backwards compat temporário).
- **Insumo.ean: novo campo** — necessário para match de XML por código de barras. VARCHAR, nullable, sem unique constraint (mesmo EAN pode ter apresentações diferentes).

### Migrations necessárias

| # | Tabela | Alteração |
|---|--------|-----------|
| 1 | `itens_consumo_interno` | Nova tabela (id, tenant_id, consumidor_id, produto_id, quantidade, custo_unitario, observacao, created_at) |
| 2 | `aliases_insumo_fornecedor` | Nova tabela (id, tenant_id, fornecedor_id, nome_nota, ean, insumo_id, created_at) + unique constraint |
| 3 | `insumos` | + coluna `ean` VARCHAR nullable |

Todas as migrations são additive.

### API contracts novos

- `POST /api/consumo-interno` — body: `{consumidor_id, produto_id, quantidade, observacao?}` → response: item criado com custo calculado
- `GET /api/consumo-interno?consumidor_id=&mes=&ano=` → lista de items
- `GET /api/consumo-interno/resumo?mes=&ano=` → `[{consumidor, itens_no_mes, total, ultima_atividade}]`
- `DELETE /api/consumo-interno/{id}` → estorno (devolve estoque)
- `POST /api/compras/importar-xml` — multipart/form-data com arquivo .xml → `{fornecedor, numero_nota, items: [{nome, ean, quantidade, unidade, custo_unitario, total, insumo_id?, status}]}`
- `POST /api/compras/confirmar-importacao` — body: `{fornecedor_id, items: [{insumo_id, quantidade, custo_unitario}], aliases: [{nome_nota, ean, insumo_id}]}` → compra criada
- `GET /api/relatorios/vendas/ticket-medio?de=&ate=` → dados de ticket médio por período
- `GET /api/relatorios/vendas/por-categoria?de=&ate=` → vendas agrupadas por categoria
- `GET /api/relatorios/vendas/por-metodo-pagamento?de=&ate=` → vendas por método
- `GET /api/relatorios/vendas/comparativo?periodo_atual=&periodo_anterior=` → comparativo
- `GET /api/relatorios/vendas/consumo-interno?mes=&ano=` → relatório de consumo interno
- `GET /api/relatorios/compras/historico?de=&ate=&fornecedor_id=` → histórico de compras
- `GET /api/relatorios/compras/gastos-por-fornecedor?de=&ate=` → ranking fornecedores
- `GET /api/relatorios/compras/evolucao-precos?insumo_id=&de=&ate=` → evolução de preço
- `GET /api/relatorios/compras/por-categoria?de=&ate=` → compras por categoria
- `GET /api/relatorios/compras/por-periodo?de=&ate=&agrupamento=` → compras por período
- `GET /api/relatorios/compras/contas-vencidas` → contas vencidas e a vencer
- `GET /api/relatorios/financeiro/fluxo-de-caixa?de=&ate=` → entradas vs saídas
- `GET /api/relatorios/financeiro/margem-por-categoria?de=&ate=` → margem por categoria
- `GET /api/relatorios/financeiro/resumo-mensal?mes=&ano=` → consolidado mensal

---

## Testing Decisions

### O que faz um bom teste aqui

Testar via endpoints HTTP (backend) e comportamento observável (frontend). Não testar funções internas diretamente.

### Módulos prioritários para testes

**Backend (maior risco)**

- `consumo_interno_service.lancar_item`: verificar que `estoque_atual` é debitado imediatamente, `MovimentoEstoque` criado com tipo correto, `custo_unitario` é snapshot do `custo_medio`.
- `consumo_interno_service.estornar_item`: verificar que estoque é devolvido e registro removido.
- `xml_parser.parse_nfe`: testar com XML real de NF-e, verificar extração correta de itens, fornecedor, número da nota.
- `xml_matcher.match_items`: testar match por EAN, match por alias, item sem match.
- `compras_service.confirmar_importacao`: verificar que compra é criada corretamente e aliases são salvos.
- Endpoints de relatórios: testar com dados seed, verificar que cálculos estão corretos (ticket médio, margem, comparativo).

**Frontend (menor risco para lógica de negócio)**

- `ImportarXmlModal`: testar fluxo completo de upload → validação → confirmação (pode ser teste e2e).
- `ConsumoInternoPage`: testar que filtros de mês/ano funcionam e totais são exibidos corretamente.

### Prior art nos testes

Seguir padrão dos testes existentes de comandas e compras no backend (pytest + fixtures de banco).

---

## Out of Scope

- **Caixa** — removido do menu, não implementar agora.
- **Dashboard personalizável com widgets** — roadmap futuro, próxima feature após v0.6.
- **Contas a Receber** — futuro, dentro de Financeiro.
- **OCR/IA para leitura de notas** — XML é suficiente, sem custo operacional.
- **Importação de XML em lote** (múltiplos arquivos de uma vez) — uma nota por vez é suficiente para o volume do cliente.
- **Exportação de relatórios para PDF/Excel** — pode ser adicionada depois, por agora visualização na tela é suficiente.
- **Notificação push quando consumo interno atinge limite** — não há conceito de limite por consumidor.
- **Fechamento mensal de consumo interno** — sem conceito de "fechar mês", só filtro por data.
- **Impressão de relatórios** — browser print é suficiente por agora.

---

## Further Notes

- A tabela `aliases_insumo_fornecedor` é um asset que cresce com o tempo. Quanto mais notas importar, menos trabalho manual nas próximas. Isso gera lock-in positivo com o sistema.
- O campo `ean` nos insumos pode ser usado futuramente para leitor de código de barras na entrada de mercadorias.
- A estrutura de 3 hubs de relatórios facilita adicionar novos relatórios sem poluir a navegação — cada hub é independente.
- O modelo flat de `itens_consumo_interno` (sem sessão) pode evoluir para suportar "cestas" ou "pedidos internos" se necessário, mas o formato atual é o mais simples para o caso de uso.
- Redirects das rotas antigas de relatórios (`/relatorios/vendas-do-dia` → `/relatorios/vendas/vendas-do-dia`) podem ser removidos após 1-2 releases.
- O parser XML de NF-e é reutilizável para qualquer futuro uso de dados fiscais (ex: integração contábil).
