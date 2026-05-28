# PRD — Melhorias Operacionais (Sprint Portela)

## Problem Statement

Operadores do sistema enfrentam cinco fricções no dia a dia:

1. **Criar comanda sem garçom cadastrado**: ao abrir nova comanda, não há como cadastrar um garçom novo sem abandonar o fluxo — obriga o usuário a navegar para Cadastros, criar o garçom, voltar e recomeçar.

2. **Sem visibilidade de capacidade de produção**: o estoque mostra quantidades brutas de insumos, mas não traduz isso em "quantos pratos consigo fazer agora". O operador precisa fazer esse cálculo manualmente na cabeça.

3. **Sem alerta proativo de estoque crítico**: insumos chegam ao nível crítico sem que ninguém seja notificado. Não há badge visual nem alerta ao abrir o sistema.

4. **Timer de comanda incorreto**: o tempo exibido desde a abertura da comanda não é real-time e pode mostrar valores errados por problema de timezone — comanda recém-aberta aparece com minutos ou horas a mais.

5. **Filtro de subcategoria inconsistente**: o filtro de categoria no cardápio não inclui subcategorias ao selecionar categoria-pai, e a tela de compras não tem filtro de categoria algum para insumos.

---

## Solution

Cinco melhorias independentes que eliminam essas fricções:

1. **Atalho de cadastro de garçom inline**: botão "+ Novo garçom" no modal de nova comanda, abrindo o modal de cadastro sem sair do fluxo. Ao salvar, o novo garçom fica automaticamente selecionado.

2. **Coluna "Produção possível" no cardápio**: cada produto exibe quantas unidades podem ser produzidas com o estoque disponível, calculado via ficha técnica.

3. **Badge de estoque crítico + toast no carregamento**: campo `nivel_critico` configurável por insumo. Badge vermelho no navbar com contagem de insumos críticos. Toast ao iniciar o app listando insumos em estado crítico.

4. **Timer real-time com timezone correto**: interval de 1 segundo, formato "Xh Ymin" / "Y min", e parse correto do `created_at` como UTC.

5. **Filtro hierárquico de subcategoria**: comportamento consistente em cardápio e compras — selecionar categoria pai inclui produtos/insumos de subcategorias. Select exibe hierarquia com indentação.

---

## User Stories

1. Como operador, quero cadastrar um garçom novo diretamente no modal de nova comanda, para não precisar abandonar o fluxo e perder o que já preenchi.
2. Como operador, quero que o novo garçom seja automaticamente selecionado após o cadastro inline, para continuar abrindo a comanda sem ação extra.
3. Como operador, quero ver no cardápio quantas unidades de cada produto posso produzir agora, para tomar decisões de cardápio sem calcular manualmente.
4. Como operador, quero que "produção possível" seja calculada com base na ficha técnica do produto, para que o número reflita a receita real.
5. Como operador, quero que produtos com ficha técnica incompleta ou insumo sem estoque mostrem 0 unidades possíveis, para não ser induzido a erros.
6. Como gestor, quero configurar um nível crítico de estoque para cada insumo, para que o sistema me avise quando aquele insumo específico estiver acabando.
7. Como operador, quero ver um badge vermelho no menu de Estoque indicando quantos insumos estão em nível crítico, para ter visibilidade periférica do problema sem precisar acessar a tela.
8. Como operador, quero receber um toast ao abrir o sistema quando há insumos em nível crítico, para ser alertado no início do turno.
9. Como operador, quero que o toast de estoque crítico mostre o nome do insumo e a quantidade restante, para saber imediatamente o que está acabando.
10. Como operador, quero que o timer da comanda aberta atualize em tempo real (a cada segundo), para acompanhar com precisão o tempo de atendimento.
11. Como operador, quero que o timer mostre "Xh Ymin" quando passa de 60 minutos, para leitura mais clara em comandas longas.
12. Como operador, quero que o timer mostre "Y min" quando está abaixo de 60 minutos, para simplicidade em atendimentos rápidos.
13. Como operador, quero que o timer mostre o tempo correto desde a abertura, sem desvio por timezone, para ter confiança no dado exibido.
14. Como operador, quero filtrar produtos no cardápio por categoria pai e ver todos os produtos das subcategorias também, para não precisar filtrar categoria por categoria.
15. Como operador, quero que o select de categoria no cardápio exiba subcategorias indentadas abaixo da categoria pai, para entender a hierarquia ao filtrar.
16. Como operador, quero filtrar insumos por categoria no modal de seleção de insumos (tela de compras), para encontrar insumos mais rapidamente.
17. Como operador, quero que o filtro de categoria em compras também inclua insumos de subcategorias ao selecionar a categoria pai, para consistência com o cardápio.

---

## Implementation Decisions

### Task 1 — Atalho garçom no modal de nova comanda

- Adicionar botão "+ Novo garçom" ao lado do select de garçom no `NovaComandaModal`
- Ao clicar, abrir `GarcomModal` em overlay (dentro do mesmo dialog ou como dialog aninhado)
- Após `onSuccess` do cadastro, invalidar query de garçons e setar o novo garçom como valor selecionado no formulário
- Nenhuma mudança de rota ou navegação

### Task 2 — Capacidade de produção

- Novo campo calculado `producao_possivel: int` retornado junto com cada produto do cardápio
- Cálculo no backend: para cada insumo da ficha técnica do produto, `floor(estoque_disponivel / quantidade_ficha)`. O mínimo entre todos os insumos é a produção possível
- Produtos sem ficha técnica cadastrada retornam `null` (exibido como "—")
- Produtos com ficha técnica mas insumo sem estoque retornam `0`
- Exibido como coluna/badge na listagem do cardápio (`CardapioPage`)
- O cálculo pode ser feito via JOIN + GROUP BY no repositório de produtos ou como computed field no service

### Task 3 — Badge de estoque crítico + toast

**Schema:**
- Novo campo `nivel_critico: Decimal | None` na tabela `insumos` (nullable — insumo sem threshold não gera alerta)
- Migration Alembic necessária

**Backend:**
- Novo endpoint `GET /api/estoque/criticos` retorna lista de insumos com `estoque_disponivel < nivel_critico`

**Frontend:**
- Query em background (ao carregar app) consumindo `/api/estoque/criticos`
- Badge vermelho no nav link de Estoque com count de resultados (oculto se count = 0)
- Clicar no badge navega para `EstoquePage` normal (sem filtro pré-aplicado)
- Toast ao montar o layout raiz: um toast por insumo crítico ("Estoque crítico: [nome] — X [unidade] restantes")
- Toast dispara apenas uma vez por sessão (controle via ref ou estado no layout)
- Campo `nivel_critico` adicionado ao `InsumoEditModal` como input numérico opcional

### Task 4 — Timer real-time

- Interval alterado de 60_000ms → 1_000ms em `ComandaAbertaPage`
- Fix de timezone: ao parsear `created_at`, garantir sufixo UTC (`iso.includes('Z') || iso.includes('+') ? iso : iso + 'Z'`)
- Função `formatTempo(ms: number): string` — retorna "Xh Ymin" se ms >= 3_600_000, senão "Y min"
- Substituir exibição atual por `formatTempo(now - new Date(created_at_utc).getTime())`
- Verificar se `ComandasPage` (listagem) tem o mesmo bug e aplicar mesmo fix
- O campo `tempo_aberta_minutos` do backend pode ser descartado no frontend (frontend calcula em tempo real)

### Task 5 — Filtro de subcategoria

**CardapioPage:**
- Substituir lógica de filtro atual por `flattenCategorias()` já existente em `useCategorias`
- Ao selecionar categoria, filtrar produtos onde `categoria_id` está na categoria selecionada OU em qualquer descendente dela
- Select exibe itens com flag `indent` para subcategorias (já suportado pelo utilitário)

**InsumoModal (compras):**
- Adicionar select de categoria usando `flattenCategorias()`
- Ao selecionar categoria, filtrar lista de insumos exibidos (cliente-side, já que todos são carregados)
- Mesmo comportamento inclusivo (pai inclui filhos)

---

## Testing Decisions

**O que faz um bom teste aqui:** testar comportamento externo observável — o que o usuário vê e o que chega/sai da API — não detalhes de implementação como nomes de função interna ou estrutura de componente.

**Módulos a testar:**

- **Cálculo de `producao_possivel`** (backend): dado um produto com ficha técnica e estoques conhecidos, o endpoint retorna o valor correto. Casos: ficha completa, ficha parcial, sem estoque, sem ficha. Testar via endpoint HTTP (teste de integração).

- **Endpoint `/api/estoque/criticos`** (backend): dado insumos com e sem `nivel_critico`, retorna apenas os que estão abaixo do threshold. Testar via endpoint HTTP.

- **Fix de timezone** (frontend/unitário): função de parse de ISO string retorna o mesmo timestamp independente de estar com ou sem `Z`.

- **`formatTempo`** (frontend/unitário): dado ms, retorna string correta para < 60 min, >= 60 min, >= 120 min.

**Prior art:** verificar se há testes existentes em `backend/tests/` para padrão de testes de endpoint.

---

## Out of Scope

- Notificação push ou email para estoque crítico
- Histórico de alertas de estoque
- Gestão de threshold em lote (editar múltiplos insumos de uma vez)
- Relatório de capacidade de produção ao longo do tempo
- Arrastar e reordenar garçons no select
- Timer em `ComandasPage` (listagem) como feature de atualização em tempo real — apenas fix de timezone se aplicável

---

## Further Notes

- Tasks 1, 4 e 5 são puramente frontend e podem ser feitas em paralelo
- Task 2 requer mudança de backend (cálculo) + frontend (exibição)
- Task 3 requer migration de banco, novo endpoint e mudanças frontend — maior esforço
- A migration do `nivel_critico` deve ser nullable para não quebrar insumos existentes
- O badge de estoque crítico na sidebar deve considerar SSE ou polling periódico para atualizar sem reload — mas dado que toast só dispara no carregamento, polling a cada N minutos é suficiente para badge
