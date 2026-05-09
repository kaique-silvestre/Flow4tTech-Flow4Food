
# Issues — Matchpoint Pós-MVP v0.1

> Gerado a partir de `docs/prds/prd_matchpoint_v0.1.md`.
> Ordem de criação respeita dependências (blockers primeiro).

---

## Issue 1 — M003: Botão ← Voltar em ComandaAbertaPage

**Tipo:** AFK  
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Adicionar botão "← Voltar" no cabeçalho de `ComandaAbertaPage` que navega para `/comandas` sem alterar o estado da comanda. O botão não deve aparecer em `FechamentoPage`. Nenhuma chamada de API — puramente navegação frontend.

### Critérios de aceite

- [x] Botão "← Voltar" visível no cabeçalho de `/comandas/:id`
- [x] Clicar no botão navega para `/comandas` (URL muda)
- [x] Comanda permanece com `status=aberta` após clicar em voltar (verificável via GET)
- [x] Botão não aparece em `FechamentoPage`
- [x] Nenhum endpoint de fechamento/cancelamento é chamado ao clicar em voltar

### User stories endereçadas

- US1: Como operador de caixa, quero um botão "← Voltar" na tela de comanda aberta, para retornar à lista de comandas sem fechar ou alterar a comanda.
- US2: Como operador, quero que o botão de voltar não apareça na tela de fechamento, para não confundir os fluxos.
- US3: Como operador, quero que a comanda permaneça com status `aberta` após eu clicar em voltar, para não perder os itens lançados.

---

## Issue 2 — M004: Helper formatQuantidade (inteiros sem decimais)

**Tipo:** AFK  
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Criar função `formatQuantidade(value: number): string` em `lib/format.ts`. Inteiros retornam sem casas decimais ("3", não "3.000"); fracionários retornam com precisão adequada (máximo 3 casas). Aplicar onde quantidades de `ItemComanda` são exibidas em `ComandaAbertaPage`. Zero impacto no backend.

### Critérios de aceite

- [x] Função `formatQuantidade` existe em `lib/format.ts`
- [x] `formatQuantidade(3)` retorna `"3"` (sem decimais)
- [x] `formatQuantidade(3.000)` retorna `"3"` (sem decimais)
- [x] `formatQuantidade(0.25)` retorna valor com casas decimais (ex: `"0.25"` ou `"0.250"`)
- [x] Quantidades na listagem de itens de `ComandaAbertaPage` usam a nova função
- [x] Teste de unidade para a função pura com entradas inteiras e fracionárias

### User stories endereçadas

- US4: Como operador, quero ver a quantidade "3" em vez de "3.000" na listagem de itens da comanda, para leitura mais rápida em horário de pico.
- US5: Como operador, quero que quantidades fracionárias (ex: 0.250) continuem sendo exibidas com precisão, para não perder informação de peso.

---

## Issue 3 — M015: NavLink prop `end` no Sidebar (destaque único)

**Tipo:** AFK  
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Adicionar prop `end` em cada `<NavLink>` da lista `NAV_ITEMS` em `Sidebar.tsx`. A prop força correspondência exata de rota, eliminando o destaque simultâneo de múltiplas abas ao navegar para sub-rotas. Nenhuma mudança de lógica de negócio.

### Critérios de aceite

- [x] Cada `NavLink` em `NAV_ITEMS` tem prop `end`
- [x] Navegar para `/historico` destaca apenas aba "Histórico" (não "Estoque" nem outra)
- [x] Navegar para qualquer rota destaca exatamente um link no sidebar
- [x] Teste: navegar para sub-rota → verificar que apenas um `NavLink` tem classe de estado ativo

### User stories endereçadas

- US6: Como operador, quero que apenas a aba correspondente à rota atual fique destacada no menu lateral, para saber sempre onde estou no sistema.
- US7: Como operador, quero que ao navegar para "Histórico" apenas a aba "Histórico" fique destacada, para navegação sem confusão.

---

## Issue 4 — M000: Reforma arquitetural — separar Item em Insumo e Produto

**Tipo:** HITL  
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Separar a entidade `Item` (com flag `vendavel`) em dois modelos distintos: `Insumo` (estoque físico, entra via Compras) e `Produto` (itens vendidos em Comandas). Inclui migrations Alembic granulares, atualização de todos os services, novos endpoints REST, atualização do frontend para usar as novas rotas, e remoção da seção "Itens" do menu. Hard cutover sem dual-write.

**Schema das novas tabelas:** ver PRD `docs/prds/prd_matchpoint_v0.1.md` — seção Fase 2.

**Sequência de migrations (9 passos, uma por arquivo Alembic):**
1. Criar `insumos`
2. Criar `produtos`
3. Criar `ficha_tecnica`
4. Migrar dados de `itens`: `vendavel=false` → `insumos`; `vendavel=true` → `produtos`
5. Migrar `componentes_ficha` → `ficha_tecnica`
6. Atualizar FK em `compras`/`itens_compra`: `item_id` → `insumo_id`
7. Atualizar FK em `itens_comanda`: `item_id` → `produto_id`
8. Atualizar FK em `movimentos_estoque`: `item_id` → `insumo_id`
9. DROP das tabelas `itens`, `fichas_tecnicas`, `componentes_ficha`

### Critérios de aceite

- [x] Tabelas `insumos`, `produtos`, `ficha_tecnica` existem com schema conforme PRD
- [x] Todos os dados de `itens` migrados corretamente (verificável via fixture)
- [x] `GET /api/insumos` retorna insumos ativos
- [x] `GET /api/produtos` retorna produtos ativos
- [x] `GET /api/itens` retorna 404
- [x] `NovaCompraPage`: seletor usa `GET /api/insumos`
- [x] `EstoquePage`: lista usa `insumos`
- [x] `ComandaAbertaPage`: seletor usa `GET /api/produtos`
- [x] Link "Itens" removido do menu Cadastros no `Sidebar`
- [x] Fechar comanda com produto com ficha técnica desconta insumos corretamente
- [x] Fechar comanda com produto sem ficha técnica fecha sem baixar estoque
- [x] Compra registrada atualiza `custo_medio` de `insumo` via média ponderada
- [x] Migrations executam em sequência completa em DB com fixture sem erro
- [x] Cada migration é reversível individualmente

### User stories endereçadas

- US1–US10 da Fase 2 (PRD `docs/prds/prd_matchpoint_v0.1.md`).

---

## Issue 5 — M001: Cardápio — CRUD de Produtos com Ficha Técnica e CMV

**Tipo:** HITL  
**Bloqueado por:** Issue 4 (M000)

### O que construir

Nova seção "Cardápio" no menu lateral com listagem de produtos, CMV colorido e formulário de criação/edição com ficha técnica dinâmica. CMV calculado no frontend a partir de `insumo.custo_medio * quantidade`. Produtos sem ficha ou com insumos sem custo médio exibem "—" no CMV.

### Critérios de aceite

- [x] Rota `/cardapio` existe e é acessível pelo menu lateral
- [x] Listagem exibe: nome, categoria, preço de venda, custo da ficha, CMV%, lucro bruto
- [x] CMV colorido: verde < 30%, amarelo 30–50%, vermelho > 50%
- [x] Criar produto com ficha técnica → aparece na listagem com CMV correto
- [x] Criar produto sem ficha técnica → CMV exibe "—"
- [x] Editar produto (nome, categoria, preço, ficha técnica) persiste no banco
- [x] Desativar produto: soft delete, produto some do seletor de comandas
- [x] Produto inativo não aparece em `GET /api/produtos` na listagem de comandas
- [x] Unidade do insumo exibida inline na ficha técnica (ex: "200 g")
- [x] CMV e custo calculados em tempo real ao montar ficha (sem salvar)
- [x] `POST /api/produtos` cria produto + ficha em transação única
- [x] `DELETE /api/produtos/:id` retorna erro se produto tem histórico em comanda

### User stories endereçadas

- US1–US12 da Fase 3 / M001 (PRD `docs/prds/prd_matchpoint_v0.1.md`).

---

## Issue 6 — M002: Cadastro rápido de Insumo inline em Nova Compra

**Tipo:** AFK  
**Bloqueado por:** Issue 4 (M000)

### O que construir

Link "[ + Cadastrar novo insumo ]" abaixo do seletor de insumos em cada linha de `NovaCompraPage`. Abre modal mínimo (nome, categoria, unidade — campos opcionais: quantidade_caixa). Ao salvar: invalida query de insumos, pré-seleciona o novo insumo na linha que disparou o modal. Dados já preenchidos na compra são preservados.

### Critérios de aceite

- [x] Link "[ + Cadastrar novo insumo ]" visível abaixo do seletor de insumo em cada linha
- [x] Clicar no link abre modal com campos: nome (required), categoria (required), unidade (required), quantidade_caixa (opcional)
- [x] Salvar no modal: insumo aparece pré-selecionado na linha que disparou o modal
- [x] Outros dados da compra (fornecedor, data, nota, outras linhas) preservados ao fechar modal
- [x] Insumo criado disponível para seleção em futuras compras (query invalidada)
- [x] `POST /api/insumos` retorna o insumo criado com ID

### User stories endereçadas

- US13–US17 da Fase 3 / M002 (PRD `docs/prds/prd_matchpoint_v0.1.md`).

---

## Issue 7 — M005: Edição inline de garçom e identificação na comanda

**Tipo:** AFK  
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Botão `[✏]` ao lado de garçom e identificação no cabeçalho de `ComandaAbertaPage`. Edição inline sem modal — campo vira input ao clicar. Confirma com Enter ou `onBlur`. Persiste via `PATCH /api/comandas/:id`. Disponível apenas para `status=aberta`.

### Critérios de aceite

- [x] Botão `[✏]` visível ao lado de identificação e garçom para comandas abertas
- [x] Clicar em `[✏]` transforma o texto em input inline (sem modal)
- [x] Enter ou blur dispara `PATCH /api/comandas/:id` com o novo valor
- [x] `PATCH` aceita `identificacao` (string) e `garcom_id` (int) individualmente
- [x] Tentativa de PATCH em comanda fechada retorna 422/400
- [x] Botão `[✏]` não renderizado para comandas com status != `aberta`
- [x] Troca de garçom reflete em relatórios de vendas por garçom
- [x] Sem debounce excessivo — salva apenas no blur/Enter, não a cada keystroke

### User stories endereçadas

- US1–US7 da Fase 4 / M005 (PRD `docs/prds/prd_matchpoint_v0.1.md`).

---

## Issue 8 — M006: Fechamento pré-preenchido (modo + valor total) ✓

**Tipo:** AFK  
**Status:** Concluída ✓ (2026-05-08)
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

`FechamentoPage` inicializa com `modo_divisao: 'sem_divisao'` e `valor` preenchido com `comanda.total` ao montar. Trocar modo de divisão reseta o campo de valor adequadamente. Zero mudança no backend.

### Critérios de aceite

- [x] `FechamentoPage` abre com "Sem divisão" já selecionado
- [x] Campo de valor já preenchido com total da comanda ao abrir
- [x] Trocar modo para "Dividir igualmente" limpa o campo de valor
- [x] Trocar de volta para "Sem divisão" preenche novamente com total da comanda
- [ ] Teste: renderizar com `total=100` → campo de valor inicia com "100" e modo "sem divisão" marcado

### User stories endereçadas

- US8–US10 da Fase 4 / M006 (PRD `docs/prds/prd_matchpoint_v0.1.md`).

---

## Issue 9 — M007: Divisão automática por N pessoas (sem perda de centavo) ✓

**Tipo:** AFK  
**Status:** Concluída ✓ (2026-05-08)
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

No modo "Dividir entre N pessoas" em `FechamentoPage`: campo `n_pessoas` + exibição de `valor_por_pessoa` calculado em tempo real. Distribuição de centavos: `Math.floor(total * 100 / n) / 100` para N-1 pessoas; última pessoa recebe o restante. N=0 ou vazio não exibe valor. Zero mudança no backend.

### Critérios de aceite

- [x] Campo `n_pessoas` visível no modo "Dividir entre N pessoas"
- [x] `valor_por_pessoa` atualizado em onChange de `n_pessoas`
- [x] Soma das partes == total da comanda (sem perda de centavos)
- [x] N=0 ou vazio: campo `valor_por_pessoa` não exibe valor
- [ ] Teste de função pura `dividirTotal(10.00, 3)` → partes somam exatamente 10.00
- [ ] Teste com R$10,00 / 3 pessoas: valores não iguais mas soma correta

### User stories endereçadas

- US11–US13 da Fase 4 / M007 (PRD `docs/prds/prd_matchpoint_v0.1.md`).

---

## Issue 10 — M008 + M011: Sidebar colapsável com ícones e botão toggle ☰ ✓

**Tipo:** AFK  
**Status:** Concluída ✓ (2026-05-08)
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Menu lateral com dois estados: expandido (ícone + texto) e colapsado (só ícone). Ícone `☰` fixo no topo alterna entre estados. Estado persiste em `localStorage` key `sidebar_collapsed`. Padrão: expandido. Tooltip ao hover em ícones no estado colapsado.

### Critérios de aceite

- [x] Ícone `☰` visível no topo do sidebar em ambos os estados
- [x] Clicar em `☰` alterna collapsed/expanded
- [x] Estado expandido: ícone + texto lado a lado em cada item
- [x] Estado colapsado: apenas ícone de cada item (sem texto)
- [x] Tooltip com nome da seção ao hover no estado colapsado (via `title` attr)
- [x] Estado padrão: expandido (`sidebar_collapsed = false`)
- [x] Estado persiste entre sessões via `localStorage`
- [x] Largura do sidebar muda visualmente (`w-14` colapsado, `w-52` expandido)
- [ ] Teste: montar com `localStorage` vazio → expandido. Clicar `☰` → collapsed. Remontar → collapsed preservado.

### User stories endereçadas

- US1–US5 da Fase 5 / M008+M011 (PRD `docs/prds/prd_matchpoint_v0.1.md`).

---

## Issue 11 — M009: Submenu de Cadastros no Sidebar

**Tipo:** AFK  
**Status:** Concluída ✓ (2026-05-08)
**Bloqueado por:** Issue 4 (M000), Issue 3 (M015)

### O que construir

Transformar item "Cadastros" em dropdown/submenu em `Sidebar.tsx` com links diretos: Categorias, Fornecedores, Garçons, Pagamentos. Remover "Itens" da lista. Submenu flutuante no estado colapsado (via onMouseEnter no ícone). Subseção ativa destacada. Remover rota `/cadastros/itens` de `App.tsx`.

### Critérios de aceite

- [x] Clicar em "Cadastros" expande submenu com: Categorias, Fornecedores, Garçons, Pagamentos
- [x] "Itens" não aparece no submenu
- [x] Navegar para `/cadastros/categorias` destaca link "Categorias" (e apenas ele)
- [x] No estado colapsado: hover no ícone de Cadastros exibe submenu flutuante
- [x] Rota `/cadastros/itens` não existe em `App.tsx` (confirmado)
- [ ] Teste: clicar "Categorias" → URL muda para `/cadastros/categorias`

### User stories endereçadas

- US6–US9 da Fase 5 / M009 (PRD `docs/prds/prd_matchpoint_v0.1.md`).

---

## Issue 12 — M010: Índice de relatórios em /relatorios

**Tipo:** AFK  
**Status:** Concluída ✓ (2026-05-08)
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Substituir `PlaceholderPage` em `/relatorios` por página índice com cards navegáveis para cada sub-relatório disponível: Vendas do Dia, Histórico de Comandas, Fechamento de Caixa, DRE, CMV por Produto, Perdas e Cortesias, Vendas por Garçom. Cada card: título + descrição de 1 linha + navegação no onClick. Sem mudança no backend.

### Critérios de aceite

- [x] `/relatorios` não exibe mais placeholder vazio
- [x] Página exibe grid de cards com todos os sub-relatórios listados
- [x] Cada card tem título e descrição de 1 linha
- [x] Clicar em card navega para a rota do relatório correspondente
- [ ] Teste: renderizar `RelatoriosIndexPage` → todos os cards presentes e rotas corretas

### User stories endereçadas

- US1–US3 da Fase 6 / M010 (PRD `docs/prds/prd_matchpoint_v0.1.md`).

---

## Issue 13 — M013: Toggle lista/cards em Comandas com localStorage

**Tipo:** AFK
**Status:** Concluída ✓ (2026-05-08)
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Toggle `[≡ Lista] / [⊞ Cards]` na tela de Comandas. Cards: CSS grid 3 colunas (telas largas) / 2 colunas (menores). Cada card exibe nome/mesa, garçom, horário de abertura, total acumulado. Clicar no card navega para `/comandas/:id`. Preferência salva em `localStorage` key `comandas_view_mode`. Zero mudança no backend ou queries.

### Critérios de aceite

- [x] Toggle visível no canto superior direito da seção de comandas
- [x] Modo lista: exibe tabela (comportamento atual)
- [x] Modo cards: grid com 3 colunas em tela larga, 2 em menor
- [x] Card exibe: nome/mesa, garçom, tempo aberto, total acumulado
- [x] Clicar no card abre `/comandas/:id`
- [x] Preferência persiste entre sessões via `localStorage`
- [ ] Teste: toggle list/cards → `localStorage` atualizado e view muda

### User stories endereçadas

- US4–US7 da Fase 6 / M013 (PRD `docs/prds/prd_matchpoint_v0.1.md`).

---

## Issue 14 — M014: Separação Histórico do dia vs Histórico geral

**Tipo:** AFK
**Status:** Concluída ✓ (2026-05-08)
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Em `ComandasPage`: seção "Histórico do dia" filtra apenas `status=fechada AND data_fechamento >= hoje_00:00`. Nova rota `/historico` com `HistoricoPage` — todas as comandas fechadas com filtros de período (data início/fim). Link "📜 Histórico" adicionado ao sidebar. Backend: confirmar/adicionar suporte a filtros de data em `GET /api/comandas`.

### Critérios de aceite

- [x] Seção "Histórico do dia" em `ComandasPage` exibe apenas comandas fechadas hoje
- [x] Rota `/historico` acessível pelo link no sidebar
- [x] `HistoricoPage` lista todas as comandas fechadas (qualquer data)
- [x] Filtro por período (data início/fim) funcional em `HistoricoPage`
- [x] `GET /api/comandas/fechadas?data_inicio=&data_fim=` retorna dados filtrados
- [x] "Histórico do dia" e "Histórico geral" não se sobrepõem
- [ ] Teste: GET com filtro do dia → retorna apenas comandas fechadas hoje

### User stories endereçadas

- US8–US11 da Fase 6 / M014 (PRD `docs/prds/prd_matchpoint_v0.1.md`).

---

## Issue 15 — M016: Dashboard revisado (remove Lucro estimado, + Histórico + calendário anual)

**Tipo:** HITL  
**Bloqueado por:** Issue 14 (M014)

### O que construir

Remover card "Lucro estimado" e heatmap mensal do Dashboard. Adicionar tabs: `[Resumo]` (cards existentes) e `[Histórico]`. Tab Histórico: tabela/gráfico de `{data, faturamento_dia, gasto_dia}` com date picker. Calendário anual: grid 12 meses × 2 linhas (Fat. / Gasto). Meses sem dados: "—". Dois novos endpoints backend.

### Critérios de aceite

- [ ] Card "Lucro estimado" removido do Dashboard
- [ ] Heatmap de dias do mês removido
- [ ] Tabs `[Resumo]` e `[Histórico]` presentes
- [ ] Tab Histórico exibe dados de entrada/saída por dia com filtro de período
- [ ] Calendário anual exibe 12 meses com faturamento e gasto por mês
- [ ] Meses sem dados exibem "—" (não R$0)
- [ ] `GET /api/dashboard/historico?inicio=&fim=` retorna `[{data, faturamento, total_compras}]`
- [ ] `GET /api/dashboard/resumo-anual?ano=` retorna array de 12 entradas `{mes, faturamento, total_compras}`
- [ ] Mês atual no calendário reflete dados em tempo real
- [ ] Teste: `GET /api/dashboard/resumo-anual` → exatamente 12 entradas

### User stories endereçadas

- US12–US17 da Fase 6 / M016 (PRD `docs/prds/prd_matchpoint_v0.1.md`).

---

## Issue 16 — M012: Subcategorias (parent_id em categorias, 2 níveis)

**Tipo:** HITL  
**Bloqueado por:** Issue 4 (M000)

### O que construir

Campo `parent_id` nullable FK em `categorias`. Máximo 2 níveis (pai + filho — sem neto). API retorna árvore `[{id, nome, children: [...]}]`. DELETE bloqueia se categoria tem filhos ativos (409). UI: accordion em `CategoriasPage`, seletor com subcategorias indentadas em modais de insumo/produto.

### Critérios de aceite

- [ ] Migration: `parent_id INTEGER NULLABLE REFERENCES categorias(id)`
- [ ] Criar subcategoria de categoria raiz: OK
- [ ] Criar subcategoria de subcategoria: retorna erro 422 (3º nível bloqueado)
- [ ] `DELETE /api/categorias/:id` com filhos ativos retorna 409
- [ ] `GET /api/categorias` retorna estrutura hierárquica com `children`
- [ ] `CategoriasPage` exibe hierarquia em accordion expansível
- [ ] `CategoriaModal`: campo opcional "Categoria pai" (Select com apenas categorias raiz)
- [ ] Seletores em modais de insumo/produto: subcategorias indentadas
- [ ] Insumos e produtos podem ser vinculados a subcategorias

### User stories endereçadas

- US1–US7 da Fase 7 / M012 (PRD `docs/prds/prd_matchpoint_v0.1.md`).

---

## Issue 17 — M017: Cálculo bidirecional Quantidade/Unitário/Total em Nova Compra

**Tipo:** AFK  
**Status:** Concluída ✓ (2026-05-09)
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Cada linha de `NovaCompraPage` tem três campos controlados: `quantidade`, `custo_unitario`, `custo_total`. Cálculo bidirecional em tempo real: editar Unitário → recalcula Total; editar Total → recalcula Unitário; editar Quantidade → recalcula Total (mantém Unitário) ou recalcula Unitário (mantém Total) dependendo de `lastEdited`. Arredondar a 2 casas decimais. Não dividir por zero. Zero mudança no schema do backend.

### Critérios de aceite

- [x] Três campos por linha: Quantidade, Custo Unitário, Custo Total
- [x] Editar Custo Unitário com Quantidade preenchida → Total calculado em tempo real
- [x] Editar Custo Total com Quantidade preenchida → Unitário calculado em tempo real
- [x] Editar Quantidade → recalcula o campo derivado correto baseado no `lastEdited`
- [x] Quantidade = 0 ou vazio → sem divisão por zero, campo derivado limpo
- [x] Resultados arredondados a 2 casas decimais
- [x] Teste: `calculateLine({quantidade: 10, custo_unitario: 2.5, lastEdited: 'unitario'})` → `custo_total: 25.00`
- [x] Teste: `calculateLine({quantidade: 10, custo_total: 25, lastEdited: 'total'})` → `custo_unitario: 2.50`
- [x] Teste: 10 / 3 → `custo_unitario` arredondado a 2 casas sem crash

### User stories endereçadas

- US8–US12 da Fase 7 / M017 (PRD `docs/prds/prd_matchpoint_v0.1.md`).
