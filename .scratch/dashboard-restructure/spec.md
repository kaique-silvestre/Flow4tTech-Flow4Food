Status: ready-for-agent

# Reestruturação do Dashboard (Matchpoint)

## Problem Statement

O dono do bar/restaurante abre o Dashboard todo dia mas ele mostra menos do que o sistema já sabe. Dados que já existem no backend (mix de forma de pagamento, ranking de garçons, perdas/cortesias, comissões pendentes) só aparecem em relatórios separados que o dono raramente abre — então decisões de margem, produtividade de equipe e vazamento de caixa ficam invisíveis no lugar onde ele realmente olha todo dia. Além disso, o card "CMV Hoje" e o card "Este mês" quebram (mostram "NaN%") quando não há faturamento no dia, o que mina confiança no painel inteiro. Nenhum card explica o que está exibindo ou de onde vem o número — o dono precisa adivinhar ou perguntar.

## Solution

Reestruturar `DashboardPage.tsx` e `dashboard_service.dashboard()` para:
1. Corrigir a divisão por zero que produz "NaN%".
2. Adicionar 6 novos widgets usando dados que já existem em `relatorio_service`/`estoque_service` (mix de pagamento, top garçons, perdas/cortesias, comissões a pagar, estoque em atenção) e enriquecer o Top 10 Produtos com faturamento + CMV%.
3. Dar a cada card/gráfico do dashboard um botão "?" que abre um popover explicando o que o widget mostra e de onde vem o dado — usando o `Popover` (`@radix-ui/react-popover`) já instalado no projeto.
4. Aplicar motion com restraint (spring crítico, sem bounce, popover materializa a partir do botão que o abriu, respeita `prefers-reduced-motion`) em vez de transições genéricas de fade/slide.

## Ordem Final dos Widgets (validada com mockup do usuário)

Topo → baixo. Cada um leva "?":

1. Alertas (banner, mantém — contas a pagar 7d / entregas esperadas / insumos críticos)
2. Faturamento Hoje
3. Lucro Estimado
4. CMV Hoje (fix: exibe "—" quando faturamento_hoje = 0, não "NaN%")
5. Ticket Médio
6. Comandas (abertas/fechadas hoje)
7. **Formas de Pagamento Hoje** *(novo)*
8. **Garçons Hoje** (top 3) *(novo)*
9. **Comissões a Pagar** *(novo)*
10. **Cortesias/Perdas do Mês** *(novo)*
11. **Estoque — Atenção** *(novo)*
12. Ontem / Esta Semana / Este Mês (3 cards, fix NaN% quando ambos zerados)
13. Comandas Abertas (lista, mantém)
14. Faturamento — Últimos 30 Dias (gráfico, mantém)
15. Faturamento por Hora (Hoje) (gráfico, mantém)
16. Top 10 Produtos (muda para ordenação por faturamento + CMV% por produto)

Lógica: hero financeiro (2-6) → "onde tá indo/vindo o dinheiro e o estoque hoje" (7-11, todos novos, agrupados) → comparativo temporal (12) → operação em tempo real (13) → séries históricas (14-16).

## User Stories

1. Como dono de bar, quero ver a margem CMV mesmo em dias sem venda ainda registrada, para não achar que o sistema está quebrado.
2. Como dono de bar, quero ver o mix de forma de pagamento (dinheiro/cartão/pix) do dia direto no dashboard, para saber quanto preciso de troco/caixa físico sem abrir o fechamento de caixa.
3. Como dono de bar, quero ver quais garçons mais venderam hoje, para reconhecer performance sem abrir o relatório de vendas por garçom.
4. Como dono de bar, quero ver o total de cortesias/perdas do mês, para identificar vazamento de margem cedo.
5. Como dono de bar, quero ver quanto tenho de comissão pendente de pagamento, para planejar o caixa da semana.
6. Como dono de bar, quero ver o Top 10 Produtos ordenado por faturamento (não só quantidade), para saber o que realmente traz dinheiro.
7. Como dono de bar, quero ver o CMV% de cada produto do Top 10, para identificar produto popular que corrói margem.
8. Como usuário de qualquer papel, quero clicar em "?" em qualquer card do dashboard e entender o que ele mostra e de onde vem o dado, sem precisar perguntar para o time técnico.
9. Como usuário com pouca familiaridade com termos financeiros, quero que a explicação do "?" use linguagem simples (não jargão de contabilidade), para entender de fato o número.
10. Como usuário em dispositivo com `prefers-reduced-motion` ativado, quero que os popovers e transições de card apareçam sem movimento brusco, para não ter desconforto visual.
11. Como usuário, quero que o popover "?" abra ancorado no botão que cliquei (não no centro da tela), para manter a relação espacial clara entre o card e a explicação.
12. Como dono de bar, quero que os cards novos carreguem com skeleton e transição suave (cross-fade), consistente com os cards existentes, para que o dashboard pareça uma coisa só, não um remendo.
13. Como dono de bar, quero que o card de comissões a pagar navegue para a tela de garçons/comissões ao clicar, assim como as comandas abertas já navegam para o detalhe.
14. Como dono de bar, quero que o card de cortesias/perdas do mês mostre o total agrupado por motivo (se houver mais de um), para saber se o problema é desperdício, cortesia de sócio, erro de lançamento, etc.
15. Como desenvolvedor, quero que os campos novos entrem em `DashboardResponse` com defaults seguros (não quebrem consumidores existentes do endpoint), para não introduzir uma mudança breaking de API.
16. Como desenvolvedor, quero que a lógica de agregação nova reutilize as funções já existentes em `relatorio_service` (`fechamento_caixa`, `vendas_por_garcom`, `perdas_cortesias`) e `estoque_service` (`get_insumos_criticos`, `get_saldo_list`) em vez de duplicar queries, para manter uma única fonte de verdade para essas métricas.
17. Como desenvolvedor, quero testes no seam `dashboard_service.dashboard()` cobrindo os novos campos com dados reais de fixture, para garantir que a agregação está correta antes de subir ao front.
18. Como desenvolvedor, quero o primeiro teste de componente React do dashboard (RTL), para estabelecer o padrão de teste de UI que o projeto ainda não tem.
19. Como dono de bar, quero ver os insumos abaixo do nível crítico configurado, para saber o que precisa comprar já.
20. Como dono de bar, quero ver os insumos com menor estoque disponível no momento (ranking, sem rótulo de "baixo"/"alto"), para bater o olho e decidir com meu próprio julgamento o que merece atenção, mesmo que ainda não tenha nível crítico cadastrado.

## Implementation Decisions

### Backend (`dashboard_service.py` / `dashboard_schemas.py`)

- Estender `DashboardResponse` com campos novos, todos com default seguro (não quebra consumidores atuais):
  - `por_metodo_pagamento_hoje: list[PagamentoResumo] = []` — reusa o schema `PagamentoResumo` já existente, mas **não** reusa a query de `fechamento_caixa`/`_build_por_metodo` (essa filtra por `comanda_id.in_(comandas_fechadas_hoje)`, o que exclui pagamento já recebido em comanda com pagamento parcial ainda aberta). **Decisão do grill**: nova query agregando `Pagamento` por `metodo_id` filtrando `Pagamento.created_at` dentro do dia corrente (mesmo padrão de `_day_utc_range` usado em todo o resto do arquivo), independente do status da comanda — reflete dinheiro/pix já recebido fisicamente hoje, que é o propósito do card ("quanto de troco eu preciso agora"). RLS por tenant já é automático via `Pagamento.tenant_id`, igual toda outra query do repositório — não precisa tratamento especial.
  - `top_garcons_hoje: list[VendasGarcomItem] = []` — reusa o schema `VendasGarcomItem` já existente em `relatorio_service`/`vendas_por_garcom` (tem exatamente os campos necessários: `garcom_id`, `garcom_nome`, `faturamento`, `qtd_comandas`, `ticket_medio`, `comissao`). Top 3 do dia chamando `vendas_por_garcom(db, hoje, hoje)` e truncando a lista — sem schema novo.
  - `perdas_cortesias_mes_total: Decimal = Decimal("0")` e `perdas_cortesias_mes_por_motivo: list[MotivoPerdaResumo] = []` (novo schema: `motivo`, `valor`) — do mês corrente, reusando `perdas_cortesias`. `motivo` é enum fechado (`MotivoPerda`), não texto livre — breakdown seguro, sem risco de explosão de categorias.
  - `comissoes_a_pagar_total: Decimal = Decimal("0")` e `comissoes_a_pagar_por_garcom: list[ComissaoGarcomResumo] = []` (novo schema pequeno: `garcom_id`, `nome`, `valor_pendente`) — soma de comissões com `pago=False` (ver `useTogglePagoComissao`/model de comissão em `garcons_repository.py`), sem filtro de data (é uma dívida em aberto, não um corte mensal). **Decisão do grill**: breakdown por garçom incluído no payload porque `/cadastros/garcons` não tem lista consolidada de pendências (só modal por garçom) — mostrar direto no card evita navegação que não resolve nada sozinha.
  - `insumos_menor_estoque: list[SaldoItemResponse] = []` — **exatamente 5** insumos (decisão do grill, não "5-8") ordenados por `estoque_disponivel` ascendente, reusando `estoque_service.get_saldo_list` (schema `SaldoItemResponse` já existente, só adicionar suporte a ordenação por `estoque_disponivel asc` no repositório/service, sem novo schema). **Exclui insumos já presentes em `insumos_criticos`** (decisão do grill: críticos e "menor estoque" não se sobrepõem no mesmo card — críticos esgota a urgência, "menor estoque" mostra o próximo nível abaixo). Não classificar como "baixo"/"alto" — é ranking cru, sem threshold inventado (decisão original do usuário, mantida).
- `ProdutoTop` já tem `faturamento` — só precisa ordenar `top_10_produtos` por faturamento em vez de quantidade, e adicionar `cmv_percentual: Optional[float]` e `classificacao_cmv: str` ao schema, reusando a lógica de `cmv_por_produto` **incluindo o tratamento de produto sem ficha técnica** (`classificacao="sem_custo"`, `cmv_percentual=None`) — não inventar um caso novo de "sem dado", seguir o padrão já estabelecido em `CMVProdutoItem`.
- Corrigir divisão por zero:
  - `cmv_hoje` / `faturamento_hoje`: quando `faturamento_hoje == 0`, front deve exibir "—" em vez de calcular `NaN`. Decisão: guard no front (`cmvPct` só calcula se `faturamento_hoje > 0`), não no backend — o backend já manda os dois valores brutos corretamente; o bug é só na divisão do componente.
  - `faturamento_mes_atual` vs `faturamento_mes_anterior`: mesma correção — função `variacao()` no front já retorna `null` quando `anterior === 0`, mas o card usa `pctMes` sem checar `atual === 0 && anterior === 0` corretamente (revisar `variacao()` para o caso dos dois zerados). Ajustar a função utilitária única, usada por todos os badges de variação.

### Frontend (`DashboardPage.tsx`)

- Novo componente `DashboardCard` (wrapper) que padroniza: título, botão "?" no canto superior direito, skeleton de loading, e slot de conteúdo — para não repetir o mesmo markup em 10+ cards. **Escopo (decisão do grill): local em `frontend/src/features/dashboard/components/`**, não em `components/ui/` — promover para compartilhado só quando uma segunda página (ex: Relatórios) precisar do mesmo padrão de "?" (YAGNI; mover depois é barato).
- Botão "?" usa `Popover`/`PopoverTrigger`/`PopoverContent` já existentes em `@/components/ui/popover.tsx`. Conteúdo do popover: texto curto (1-2 frases) explicando o widget + a fonte do dado (ex: "Soma dos pagamentos registrados no fechamento das comandas de hoje, por forma de pagamento."). Texto vive como prop `helpText` no `DashboardCard`, não hardcoded espalhado.
- Novo card "Formas de Pagamento Hoje": donut chart (Recharts `PieChart`) usando `por_metodo_pagamento_hoje`.
- Novo card "Garçons Hoje" (top 3): lista simples com nome + faturamento, usando `top_garcons_hoje`.
- Novo card "Cortesias/Perdas do Mês": valor total + breakdown por motivo (lista pequena), usando `perdas_cortesias_mes_total`/`_por_motivo`.
- Novo card "Comissões a Pagar": valor total + **breakdown por garçom direto no card** (lista curta nome + valor pendente, usando `comissoes_a_pagar_por_garcom` — decisão do grill, já que `/cadastros/garcons` não consolida pendências). Mantém clicável → navega para `/cadastros/garcons` como atalho complementar, não como única forma de ver o detalhe.
- Novo card "Estoque — Atenção": duas seções no mesmo card — (a) críticos, reusando os mesmos itens de `insumos_criticos` que já alimentam o banner de alerta (não duplicar UI de lista, extrair um subcomponente `InsumoCriticoRow` reusável entre banner e card); (b) "Menor estoque" (exatamente 5 itens, já excluindo os que aparecem em críticos — vem pronto assim do backend), lista simples nome + `estoque_disponivel` + `unidade_base` de `insumos_menor_estoque`, sem badge de cor/rótulo de severidade.
- Top 10 Produtos: trocar eixo/ordenação para faturamento, e mostrar CMV% ao lado de cada barra (tooltip ou label secundário).
- Motion (seguindo `apple-design`):
  - Popover materializa a partir do botão "?" que o disparou (`transform-origin` ancorado no trigger — comportamento padrão do Radix Popover já faz isso, então garantir que nenhum CSS custom sobrescreva isso).
  - Transição de spring criticamente amortecido (`damping: 1.0`, sem bounce) para abrir/fechar popover — informacional, sem gesto de arrasto, então nunca usar bounce.
  - Loading→conteúdo dos cards novos: cross-fade (opacity), nunca slide — consistente com o padrão implícito dos cards existentes (`CardSkeleton`).
  - Respeitar `prefers-reduced-motion: reduce`: cross-fade vira transição de opacidade curta sem spring.
- Stack já suporta tudo isso sem instalar nada novo: shadcn já configurado (`components.json`), Tailwind 3.4 (não 4 — ignorar o CSS de exemplo em Tailwind 4 syntax que foi mencionado na conversa), `Popover` do Radix já instalado, `Card` já no padrão shadcn default. **Não** portar o componente `hero-195`/`BorderBeam` sugerido pelo usuário — é um componente de hero de marketing (landing page), não se aplica a um dashboard de KPIs denso; o `Card` que ele traz já é idêntico ao `Card` existente no projeto. **Decisão do grill: `BorderBeam` fica fora, decidido, não adiado** — dashboard denso de KPI não precisa de animação decorativa; risco de distrair mais que ajudar.

### Dados de negócio ausentes (fora do escopo mas registrados)

- Meta de faturamento mensal configurável — não existe hoje, ficaria em spec futura.

## Testing Decisions

- Um bom teste aqui testa comportamento externo: dado um estado de banco (comandas fechadas com pagamentos, comissões, cortesias), o `dashboard_service.dashboard()` retorna os totais corretos — não testar como a query SQL é montada internamente.
- **Seam backend**: estender `backend/tests/test_dashboard.py` (já existe, testa `dashboard_service.dashboard()` via fixtures de comandas/pagamentos). Adicionar casos para:
  - `por_metodo_pagamento_hoje` incluindo o caso crítico do grill: comanda com pagamento parcial hoje que **não** fechou (status permanece aberto/reaberto) — o pagamento parcial deve aparecer no total por método mesmo assim (prova que a nova query não reusa o filtro de `fechamento_caixa`).
  - `top_garcons_hoje` (top 3, ordenado por faturamento).
  - `perdas_cortesias_mes_total`/`_por_motivo`.
  - `comissoes_a_pagar_total`/`_por_garcom`.
  - `insumos_menor_estoque`: ordenação correta por `estoque_disponivel` asc, exatamente 5 itens, e caso em que um insumo crítico **não** aparece duplicado na lista de menor estoque.
  - `top_10_produtos` ordenado por faturamento com `cmv_percentual`, incluindo produto sem ficha técnica (`cmv_percentual=None`, `classificacao_cmv="sem_custo"`).
  Prior art de agregação similar: `backend/tests/test_relatorios_financeiros.py` (`test_cmv_classificacao_faixas`, `test_perdas_agrupadas_por_motivo`) e `backend/tests/test_estoque.py` (fixtures de insumo/nivel_critico) — mesmo padrão de fixture (`_criar_produtos_com_ficha`, `_set_custo_medio`) deve ser reutilizado em vez de recriado.
- **Seam frontend (novo)**: primeiro teste RTL do dashboard, `frontend/src/features/dashboard/DashboardPage.test.tsx`. Mocka `useDashboard` (como `usePlatformApi.test.tsx` já mocka hooks similares — usar de prior art de estrutura de mock/wrapper). Casos mínimos: (a) todos os cards novos renderizam com dados mockados; (b) clicar no "?" de um card abre popover com o `helpText` esperado; (c) card com `faturamento_hoje: 0` não renderiza "NaN%" em nenhum lugar da tela.
- Não é necessário E2E/Playwright novo — não há suite E2E no projeto hoje; RTL + backend cobre o comportamento.

## Out of Scope

- Meta de faturamento configurável (feature nova, sem dado/schema hoje).
- Qualquer endpoint novo — tudo entra dentro do payload existente de `GET /dashboard`.
- Portar `hero-195`/`BorderBeam` como estão (componentes de marketing/hero) — só avaliar `BorderBeam` como acento opcional pontual, não como padrão do dashboard.
- Migração para Tailwind 4 (projeto está em 3.4; o CSS de exemplo trazido pelo usuário é de Tailwind 4 e não se aplica sem uma migração maior, fora de escopo aqui).
- Dashboard mobile/responsivo além do que já existe (grid já é responsivo via Tailwind, não mexer no breakpoint strategy).
- Classificação de estoque "alto"/excesso de capital parado — **decisão explícita do usuário**: não inventar threshold sem campo de nível ideal/máximo no schema. Card de estoque mostra só críticos (já configurados) + ranking cru por menor quantidade disponível.
- Novo campo `nivel_ideal`/`estoque_maximo` no model `Insumo` — não entra nesta spec; se o dono quiser classificação "alto" no futuro, é spec própria com migration.
- Card "Saídas Hoje" (contas pagas hoje + comissões pagas hoje, fluxo de caixa real vs. accrual) — **usuário recusou** ("Não") quando proposto nesta conversa. Registrado aqui só para não ser reproposto sem contexto.
- Unificar o sistema de banner de alertas (calculado ao vivo) com o sistema de notificações persistidas (tabela `Notificacao`, hoje só com o tipo `entrega_prevista`) — são dois sistemas paralelos identificados durante a análise, mas unificá-los é reforma maior, fora desta spec.
- Novos tipos de alerta além dos já existentes (conta vencida — diferente de "vencendo em 7 dias" —, CMV/perdas acima de threshold, comanda aberta há muito tempo como alerta ativo) — levantados na conversa como possibilidades, não pedidos para esta spec.

## Further Notes

- `/setup-matt-pocock-skills` ainda não foi finalizado nesta sessão (perguntas foram respondidas — GitHub como tracker, labels default, guardrails não — mas os arquivos em `docs/agents/` não foram escritos). **Esta spec usa `.scratch/` local por instrução explícita do usuário nesta conversa** (override pontual da resposta anterior de "GitHub"), não porque o tracker do projeto tenha sido decidido como local. Se quiser tornar `.scratch/` o tracker permanente do projeto, rodar `/setup-matt-pocock-skills` de novo e escolher "Local markdown" na Seção A.
- `apple-design` consultado: para popover informacional (sem gesto de arrasto), usar sempre spring criticamente amortecido sem bounce; bounce só se algum dia houver um card arrastável/flick. Ancorar `transform-origin` no botão "?", nunca centralizar. Cross-fade para loading→conteúdo, nunca slide.
- Bug NaN% já era visível ao vivo em `localhost:5173` com tenant de teste (faturamento_hoje = 0): card "CMV Hoje" mostrava "NaN%", card "Este mês" mostrava "↓NaN% vs mês passado".
- **Grill de pré-implementação realizado** (skill `grilling`). Fatos levantados por exploração direta de código (não graphify — buscas pontuais, grep/Read foram mais rápidos que consulta ao grafo para essas perguntas específicas):
  1. `fechamento_caixa`/`_build_por_metodo` filtra por comandas com `status=FECHADA`, excluindo pagamento parcial em comanda ainda aberta → decisão: nova query por `Pagamento.created_at`, não reuso direto.
  2. `vendas_por_garcom` já retorna o schema necessário (`VendasGarcomItem`) → sem schema novo pra garçons.
  3. `cmv_por_produto` já trata produto sem ficha técnica (`classificacao="sem_custo"`) → Top 10 segue o mesmo padrão.
  4. `motivo` de perda é enum fechado (`MotivoPerda`), não texto livre → breakdown por motivo é seguro.
  5. `/cadastros/garcons` não tem lista consolidada de comissões pendentes → card de comissões ganhou breakdown por garçom embutido.
  Decisões tomadas (todas aceitando a recomendação proposta, sem contestação do usuário): pagamento hoje = por `created_at` real; comissões a pagar = breakdown por garçom no card; menor estoque = exatamente 5 itens, sem sobrepor com críticos; BorderBeam = não, decidido (não mais "avaliar depois"); `DashboardCard` = escopo local em `features/dashboard/`, não promovido a `components/ui/` ainda.
