# PRD: Compras Agendadas + Contas a Pagar

## Problem Statement

Hoje o sistema de compras registra apenas compras imediatas — o produto entra no estoque no momento do lançamento e o pagamento é considerado já realizado. Isso impede o gestor de:

1. **Registrar pedidos futuros** (encomendas que serão entregues em outra data)
2. **Comprar a prazo** (recebe agora, paga depois)
3. **Rastrear obrigações financeiras futuras** (saber quanto deve, para quem e quando)
4. **Antecipar chegadas de mercadoria** (saber o que está a caminho e quando esperar)

O resultado é falta de visibilidade financeira e operacional: o gestor não sabe o que deve, não sabe o que está chegando, e descobre vencimentos de contas de surpresa.

## Solution

Estender o módulo de Compras para suportar dois novos fluxos:

- **Compra agendada (pedido futuro):** produto encomendado, chegará em data futura, pagamento também futuro. O estoque só é atualizado quando o recebimento é confirmado.
- **Compra a prazo:** produto recebido imediatamente, pagamento com vencimento futuro. O estoque é atualizado na hora, mas a obrigação financeira fica registrada como conta a pagar.

Criar módulo de **Contas a Pagar** para rastrear todas as obrigações financeiras originadas de compras, com filtros por status, vencimento e fornecedor, e integração no dashboard com alertas de vencimento e de entregas esperadas.

Um job diário (APScheduler embutido no FastAPI) verifica compras com data de recebimento prevista para hoje ou antes, e exibe notificação no dashboard pedindo confirmação manual do recebimento.

## User Stories

### Criação de Compras

1. Como gestor, quero criar uma compra agendada informando a data prevista de recebimento, para registrar pedidos feitos antecipadamente sem impactar o estoque imediatamente.
2. Como gestor, quero criar uma compra a prazo onde o produto é recebido agora mas o pagamento tem vencimento futuro, para controlar compras feitas no crédito com fornecedores.
3. Como gestor, quero informar a data de vencimento do pagamento ao criar qualquer compra, para que o sistema saiba quando cobrar minha atenção sobre essa obrigação.
4. Como gestor, quero escolher o tipo de compra (imediata, agendada, a prazo) no formulário de nova compra, para registrar corretamente o fluxo de cada transação.
5. Como gestor, quero editar uma compra agendada (itens, quantidades, fornecedor, datas) enquanto ela ainda não foi recebida, para corrigir erros ou atualizar condições negociadas.
6. Como gestor, quero que uma compra fique bloqueada para edição após o recebimento ser confirmado, para garantir integridade dos dados de estoque e financeiro.

### Recebimento de Mercadoria

7. Como gestor, quero confirmar manualmente o recebimento de uma compra agendada, para que o estoque seja atualizado no momento real da entrega.
8. Como gestor, quero ver no dashboard um alerta para cada compra com entrega prevista para hoje ou datas anteriores ainda não recebida, para não perder o acompanhamento de pedidos em aberto.
9. Como gestor, quero registrar a data real de recebimento ao confirmar uma entrega, para ter histórico de pontualidade dos fornecedores.
10. Como gestor, quero que ao confirmar o recebimento o custo médio dos insumos seja recalculado automaticamente, mantendo consistência com o comportamento atual do sistema.

### Contas a Pagar

11. Como gestor, quero ver uma lista de todas as contas a pagar com filtros por status (pendente, pago, vencido), período de vencimento e fornecedor, para ter visão clara das minhas obrigações financeiras.
12. Como gestor, quero registrar o pagamento de uma conta informando o método de pagamento e a data em que foi pago, para manter histórico financeiro completo.
13. Como gestor, quero que ao cancelar uma compra agendada (antes do recebimento) as contas a pagar vinculadas sejam automaticamente canceladas, para não ter obrigações fantasmas no sistema.
14. Como gestor, quero que contas com vencimento ultrapassado apareçam automaticamente com status "vencido" sem precisar de ação manual, para identificar rapidamente obrigações atrasadas.
15. Como gestor, quero ver o valor total de contas pendentes e vencidas na tela de Contas a Pagar, para ter visão rápida da exposição financeira.
16. Como gestor, quero adicionar uma observação ao registrar pagamento de uma conta, para documentar contexto (ex: "pago via transferência agendada").

### Dashboard e Visibilidade

17. Como gestor, quero ver no dashboard um card "Contas vencendo nos próximos 7 dias" com valor total e quantidade, para antecipar pagamentos sem precisar entrar na tela de contas.
18. Como gestor, quero ver no dashboard um card "Entregas esperadas nos próximos 7 dias" com lista de compras agendadas pendentes de recebimento, para planejar o espaço e a operação.
19. Como gestor, quero ver um badge no menu lateral de "Contas" indicando quantas contas estão vencidas ou vencem hoje, para ter visibilidade periférica sem precisar acessar a tela.
20. Como gestor, quero que contas a pagar apareçam nos relatórios de despesas, para ter visão financeira completa do negócio.

### Cancelamentos

21. Como gestor, quero cancelar uma compra agendada antes do recebimento, para registrar pedidos que não foram entregues ou foram cancelados com o fornecedor.
22. Como gestor, quero que o cancelamento de compra antes do recebimento não gere estorno de estoque, já que o produto nunca entrou no sistema.

## Implementation Decisions

### Esquema de Banco de Dados

**Tabela `compras` — campos novos:**
- `tipo_compra`: enum (`imediata`, `agendada`, `a_prazo`)
- `status`: enum estendido (`rascunho`, `confirmado`, `recebido`, `pago`, `cancelado`) — substitui o atual `ativa/cancelada`
- `data_prevista_recebimento`: date, nullable
- `data_real_recebimento`: date, nullable
- `data_prevista_pagamento`: date, nullable (vencimento do pagamento)

**Nova tabela `contas_pagar`:**
- `id`: int PK
- `compra_id`: int FK → compras, nullable (permite contas manuais futuras)
- `fornecedor_id`: int FK → fornecedores, nullable
- `valor`: Decimal(12,2)
- `data_vencimento`: date
- `data_pagamento`: date, nullable
- `status`: enum (`pendente`, `pago`, `vencido`, `cancelado`)
- `metodo_pagamento_id`: int FK → metodos_pagamento, nullable
- `observacao`: str, nullable
- `created_at`: datetime

### Módulos Backend

**`compras_service` — modificações:**
- `criar_compra()`: aceita `tipo_compra`, `data_prevista_recebimento`, `data_prevista_pagamento`. Se `tipo_compra = imediata`, mantém comportamento atual (entra estoque + status recebido). Se `agendada`, status = `confirmado`, sem movimentar estoque. Se `a_prazo`, entra estoque imediatamente + cria conta a pagar.
- `confirmar_recebimento(compra_id)`: valida status = `confirmado`, move estoque, atualiza custo médio, seta `data_real_recebimento`, muda status para `recebido`.
- `cancelar_compra()`: se status = `confirmado` (sem estoque), apenas cancela + cancela contas vinculadas. Se `recebido`, mantém comportamento atual de estorno.

**Novo módulo `contas_pagar_service`:**
- `criar_conta(compra_id, valor, data_vencimento)`: cria registro em `contas_pagar`
- `pagar_conta(conta_id, metodo_pagamento_id, data_pagamento, observacao)`: valida status pendente/vencido, registra pagamento
- `cancelar_conta(conta_id)`: cancela conta vinculada a compra cancelada
- `list_contas(status, data_vencimento_inicio, data_vencimento_fim, fornecedor_id)`: listagem com filtros
- `atualizar_status_vencidos()`: chamado pelo scheduler — marca como `vencido` contas com `data_vencimento < hoje` e status `pendente`

**Novo módulo `scheduler`:**
- APScheduler BackgroundScheduler embutido no FastAPI lifespan
- Job 1 (diário 8h): verificar compras com `data_prevista_recebimento <= hoje` e status `confirmado` → gerar notificações pendentes
- Job 2 (diário 8h): `atualizar_status_vencidos()` em contas a pagar

**Novo módulo `notificacoes_service`:**
- Interface simples: `criar_notificacao(tipo, referencia_id, mensagem)`
- `list_notificacoes_pendentes()`: retorna notificações não lidas para o dashboard
- `marcar_lida(notificacao_id)`
- Tipos: `entrega_prevista`, `conta_vencendo`

**`dashboard_service` — modificações:**
- Adicionar: `contas_vencendo_7_dias()` → total e quantidade
- Adicionar: `entregas_esperadas_7_dias()` → lista de compras agendadas pendentes

**`relatorios_service` — modificações:**
- Incluir `contas_pagar` com status `pago` nos relatórios de despesas por período

### Módulos Frontend

**`ComprasPage` — modificações:**
- Adicionar filtro por `tipo_compra` e `status` (expandir além de ativa/cancelada)
- Botão "Confirmar Recebimento" para compras com status `confirmado`
- Indicador visual de tipo de compra na listagem

**`NovaCompraPage` — modificações:**
- Seletor de `tipo_compra`
- Campo `data_prevista_recebimento` (obrigatório se agendada)
- Campo `data_prevista_pagamento` / `data_vencimento` (obrigatório se agendada ou a_prazo)

**Nova página `ContasPagarPage`:**
- Listagem com filtros: status, período de vencimento, fornecedor
- Totalizadores: total pendente, total vencido
- Ação "Registrar Pagamento" com modal (método, data, observação)
- Badge no menu lateral com contagem de vencidas/vencendo hoje

**`Dashboard` — modificações:**
- Card "Contas vencendo (7 dias)"
- Card "Entregas esperadas (7 dias)"
- Seção de notificações pendentes com ação de confirmação de recebimento

### API Contracts

**Compras:**
- `POST /api/compras` — aceita `tipo_compra`, `data_prevista_recebimento`, `data_prevista_pagamento`
- `POST /api/compras/{id}/confirmar-recebimento` — confirma recebimento, move estoque
- `GET /api/compras` — filtros adicionais: `tipo_compra`, `status` (agora multi-valor)

**Contas a Pagar:**
- `GET /api/contas-pagar` — filtros: `status`, `data_vencimento_inicio`, `data_vencimento_fim`, `fornecedor_id`
- `POST /api/contas-pagar/{id}/pagar` — body: `metodo_pagamento_id`, `data_pagamento`, `observacao`
- `GET /api/contas-pagar/resumo` — totais por status (usado no badge e dashboard)

**Notificações:**
- `GET /api/notificacoes` — lista notificações pendentes
- `POST /api/notificacoes/{id}/marcar-lida`

## Testing Decisions

**O que torna um bom teste aqui:** testar comportamento externo observável — o que entra no estoque, o que aparece nas contas, o que o scheduler produz — não a estrutura interna dos serviços.

**Módulos a testar:**

- `compras_service.confirmar_recebimento()`: verifica que estoque do insumo aumenta corretamente, custo médio recalcula, movimento de estoque é registrado, status muda para `recebido`.
- `compras_service.criar_compra(tipo=agendada)`: verifica que estoque NÃO muda, status = `confirmado`, conta a pagar criada com vencimento correto.
- `compras_service.criar_compra(tipo=a_prazo)`: verifica que estoque aumenta imediatamente, conta a pagar criada.
- `compras_service.cancelar_compra()` com status `confirmado`: verifica que estoque não é alterado, contas vinculadas ficam com status `cancelado`.
- `contas_pagar_service.pagar_conta()`: verifica que status muda para `pago`, data e método registrados.
- `contas_pagar_service.atualizar_status_vencidos()`: verifica que contas com `data_vencimento < hoje` e status `pendente` viram `vencido`.

**Prior art:** ver testes existentes em `backend/tests/` para padrão de fixtures de banco e asserções de serviço.

## Out of Scope

- **Parcelamento de contas:** MVP suporta parcela única. Múltiplos vencimentos por compra ficam para v2.
- **Contas a receber:** módulo financeiro de receitas não faz parte deste PRD.
- **Aprovação de pedidos:** sem fluxo de aprovação multi-usuário — gestor único confirma.
- **Integração com notas fiscais eletrônicas (NF-e):** lançamento manual apenas.
- **Notificações por email/SMS:** alertas somente no dashboard e menu lateral.
- **Fluxo de caixa projetado:** relatório de projeção de caixa baseado em contas a pagar/receber fica para versão futura.

## Further Notes

- **Migração de dados:** compras existentes com status `ativa` devem ser migradas para `tipo_compra = imediata` e `status = recebido`. Compras com status `cancelada` → `status = cancelado`.
- **APScheduler:** inicializar no lifespan do FastAPI (`@asynccontextmanager`) para garantir shutdown limpo. Usar `BackgroundScheduler` com trigger `cron`.
- **Badge de contas:** seguir padrão do badge de estoque crítico já implementado — endpoint de resumo chamado no carregamento do layout, exibido no item de menu.
- **Vencimento automático:** status `vencido` é calculado pelo job do scheduler, não em tempo real na query — aceitar defasagem de até 24h é aceitável para MVP.
