# PRD — Flow4Food V2: Permissões V1.5, Painel Admin Global, Calendário, Promoções e Cockpit Consolidado

## Problem Statement

O Flow4Food V1 entrega multi-tenancy, billing e auditoria de caixa, mas apresenta quatro lacunas que limitam escala comercial e operacional:

1. **Permissões rígidas:** perfis Admin/Gerente/Caixa são hardcoded. O dono do restaurante não consegue criar um perfil personalizado ("Garçom Sênior") nem aplicar um padrão pré-configurado a novos funcionários sem editar código. Mudar permissões de um perfil existente exige deploy.

2. **Sem visibilidade para os donos do SaaS:** não existe painel onde a Flow4Tech veja todas as empresas cadastradas, gerencie assinaturas e ative/suspenda clientes. Tudo é feito via acesso direto ao banco.

3. **Sem planejamento de agenda:** o estabelecimento não tem onde registrar eventos futuros (casamentos, shows, festivais) integrados ao sistema. Esses eventos ficam em papel ou WhatsApp, sem visibilidade para a equipe.

4. **Sem promoções sistematizadas:** descontos são aplicados manualmente a cada lançamento. Não há mecanismo para criar uma promoção recorrente ("Terça do Chopp") que aplique desconto automaticamente no PDV durante a janela de horário válida.

5. **Gestão fragmentada:** contas a pagar, entregas de fornecedores, eventos e promoções vivem em abas separadas. O gerente precisa de um cockpit único que cruze essas informações por data.

---

## Solution

Cinco módulos entregues em sequência, todos sobre a base V1 existente:

1. **Permissões V1.5:** templates de perfil pré-configurados + perfis totalmente customizáveis por tenant + suporte a "usuário livre" (sem perfil). Mantém o modelo de telas existente; sem big-bang de migração.

2. **Painel Admin Global:** interface exclusiva da Flow4Tech para listar tenants, ver usuários por empresa e ativar/suspender assinaturas. Autenticação separada dos usuários cliente; banco acessado via role com BYPASSRLS.

3. **Calendário de Eventos:** aba visual para agendar eventos por data. Modal de criação rápida ou via clique na data. Base para os módulos seguintes.

4. **Motor de Promoções:** criar promoções com janela de horário e recorrência (semanal/mensal). Aplicação automática de desconto no PDV quando as condições são satisfeitas.

5. **Cockpit Consolidado:** calendário único com quatro camadas (eventos, promoções, contas a pagar, entregas). Toggles de filtro por camada. Deep link para as telas originais ao clicar em cada card.

---

## User Stories

### §1 — Permissões V1.5

1. Como administrador do tenant, quero criar um perfil de acesso personalizado escolhendo quais telas do sistema estão liberadas, para que eu possa dar acesso cirúrgico a um funcionário que não se encaixa nos perfis padrão.
2. Como administrador do tenant, quero aplicar um template de perfil pré-configurado ao criar um novo funcionário, para não precisar configurar telas manualmente a cada contratação.
3. Como administrador do tenant, quero ver qual template um perfil está seguindo, para entender de onde vieram as permissões sem precisar verificar tela a tela.
4. Como administrador do tenant, quero desvincular um perfil de um template para editá-lo manualmente, sem perder as permissões que o template definiu como ponto de partida.
5. Como administrador do tenant, quero criar um usuário "livre" sem associá-lo a um perfil, configurando as telas diretamente no usuário para casos pontuais.
6. Como administrador do tenant, quero que alterações em um perfil reflitam no acesso do funcionário na próxima vez que ele fizer login, sem precisar forçar logout manual.
7. Como funcionário, quero que meu acesso seja revogado ou atualizado em até 15 minutos após o administrador alterar meu perfil, para que a mudança seja efetiva rapidamente.
8. Como administrador da plataforma Flow4Tech, quero que novos templates do sistema sejam aplicados automaticamente a todos os perfis vinculados a eles no próximo refresh de token, para propagar padrões sem intervenção manual por tenant.
9. Como administrador do tenant, quero que perfis hardcoded existentes (Admin, Gerente, Caixa) continuem funcionando após a migração para V1.5, agora como templates de sistema.
10. Como desenvolvedor, quero uma migration segura e reversível para V1.5 que não quebre tokens ativos nem exija downtime.

### §2 — Painel Admin Global

11. Como admin da Flow4Tech, quero fazer login em um painel separado do app cliente, com credenciais próprias, para ter acesso consolidado sem misturar identidade com tenants.
12. Como admin da Flow4Tech, quero ver uma lista de todas as empresas cadastradas com nome, CNPJ, status da assinatura e data de vencimento, para monitorar a base de clientes.
13. Como admin da Flow4Tech, quero filtrar empresas por status de assinatura (trial, ativa, suspensa, cancelada), para focar nas que precisam de atenção.
14. Como admin da Flow4Tech, quero ver os usuários cadastrados em uma empresa específica com nome, username, perfil e último login, para suporte e auditoria.
15. Como admin da Flow4Tech, quero suspender ou reativar a assinatura de um tenant com um clique, para bloquear acesso de inadimplentes ou liberar após pagamento.
16. Como admin da Flow4Tech, quero que a suspensão de assinatura bloqueie o acesso dos usuários do tenant em até 15 minutos (próximo refresh de token), sem precisar invalidar tokens manualmente.
17. Como admin da Flow4Tech, quero que o painel use uma conexão de banco separada que ignora RLS, para ver dados de todos os tenants sem configuração especial por empresa.
18. Como admin da Flow4Tech, quero que qualquer tentativa de acesso ao painel sem credenciais de plataforma válidas retorne 403 imediatamente, para que o isolamento de dados nunca dependa de um "if" esquecido.

### §3.X — Calendário de Eventos

19. Como gerente, quero ver um calendário visual mensal com os eventos agendados do meu estabelecimento, para planejar escalas e recursos com antecedência.
20. Como gerente, quero criar um evento clicando em uma data no calendário, com o campo de data pré-preenchido e travado, para evitar erros de digitação.
21. Como gerente, quero criar um evento via botão "+", preenchendo título, descrição e data manualmente, para agendar eventos sem precisar navegar no calendário.
22. Como gerente, quero editar o título e descrição de um evento existente, para corrigir informações após criação.
23. Como gerente, quero excluir um evento, para remover agendamentos cancelados ou equivocados.
24. Como gerente, quero navegar entre meses no calendário, para visualizar eventos futuros e passados.
25. Como garçom, quero ver o calendário de eventos mas sem poder criar ou editar, para me informar sobre eventos do dia sem risco de alteração acidental.

### §3.Y — Motor de Promoções

26. Como gerente, quero criar uma promoção com nome, tipo de desconto (porcentagem ou valor fixo), valor, período de vigência e janela de horário, para configurar ofertas com antecedência.
27. Como gerente, quero configurar uma promoção com recorrência semanal em dias específicos da semana, para promoções fixas como "Terça do Chopp".
28. Como gerente, quero configurar uma promoção com recorrência mensal em dias específicos do mês, para promoções como "todo dia 15".
29. Como gerente, quero associar múltiplos produtos de cardápio a uma promoção, para criar pacotes ou ofertas de categoria.
30. Como gerente, quero ver a lista de promoções ativas e futuras com seus detalhes de vigência e recorrência, para monitorar o que está sendo praticado.
31. Como gerente, quero encerrar uma promoção antes do prazo original, para responder a mudanças de estratégia.
32. Como operador de caixa/garçom, quero que o desconto da promoção seja aplicado automaticamente ao lançar um item na comanda quando a promoção está ativa, sem precisar selecionar manualmente.
33. Como operador de caixa, quero saber qual promoção foi aplicada a um item da comanda, para explicar ao cliente o desconto concedido.
34. Como gerente, quero que produtos em múltiplas promoções ativas simultâneas recebam o desconto da promoção mais antiga (menor ID), com comportamento previsível e documentado.
35. Como gerente, quero ver as promoções representadas no calendário visual (camada verde), para ter visão integrada de agenda e atividade comercial.

### §3.Z — Cockpit Consolidado

36. Como gerente, quero ver em um único calendário os eventos agendados, promoções ativas, contas a pagar com vencimento e entregas de fornecedores esperadas, para ter visão operacional do dia sem trocar de aba.
37. Como gerente, quero filtrar o calendário por tipo de informação via toggles (ligar/desligar cada camada), para focar no que é relevante no momento.
38. Como gerente financeiro, quero clicar em um card de conta a pagar no calendário e ver valor e código de barras em um modal rápido, para pagar sem sair do calendário.
39. Como gerente financeiro, quero um botão "Ir para o Financeiro" no modal da conta, para acessar o registro completo quando precisar de mais detalhes.
40. Como gerente de estoque, quero clicar em um card de entrega no calendário e ver os insumos esperados, para me preparar para o recebimento.
41. Como gerente de estoque, quero um botão "Dar Entrada no Estoque" no card de entrega, para iniciar o processo de recebimento diretamente do calendário.
42. Como operador de caixa, quero que cards de contas a pagar e entregas sejam omitidos do meu calendário se eu não tiver acesso às telas de financeiro e estoque, para não ver dados que não são da minha responsabilidade.
43. Como gerente, quero que compras confirmadas (pedido feito, não recebido) apareçam como entregas esperadas no calendário, para saber o que chega e quando.

---

## Implementation Decisions

### §1 — Permissões V1.5

**Novas tabelas:**
- `permission_templates`: catálogo de templates (nome, descrição, `is_system`)
- `template_permissions`: telas por template (template_id, screen, can_access)
- `user_permissions`: telas por usuário livre (user_id, screen, can_access)

**Alterações em tabelas existentes:**
- `profiles`: adicionar coluna `template_id BIGINT REFERENCES permission_templates(id)` (nullable). `NULL` = perfil custom; não-null = travado no template.
- `system_users`: tornar `profile_id` nullable. `NULL` = usuário livre (usa `user_permissions`).

**Resolução de permissões ao montar JWT:**
- `profile.template_id IS NOT NULL` → lê de `template_permissions` (nunca copia para `profile_permissions`)
- `profile.template_id IS NULL` → lê de `profile_permissions` (custom)
- `user.profile_id IS NULL` → lê de `user_permissions`
- Ausência de registro = acesso negado

**Estratégia de JWT:**
- Access token: 15 minutos (ajustar `JWT_EXPIRES_MINUTES` no settings)
- Permissões recomputadas a cada `rotate_refresh_token` — mudança de perfil/template propaga em até 15min
- Sem leitura de banco por request; `require_permission(screen)` permanece inalterado

**Migração V1 → V1.5:**
- Perfis fixos existentes viram templates de sistema (`is_system = TRUE`) em `permission_templates`
- `template_permissions` populada com os dados atuais de `profile_permissions` de cada perfil padrão
- `profiles.template_id` preenchido para perfis que eram hardcoded
- `system_users.profile_id` permanece NOT NULL para todos os usuários existentes
- Migration reversível com Alembic; zero downtime

**UI:**
- Tela de edição de perfil: seletor de template no topo. Se template ativo, checkboxes de telas são read-only. Botão "Personalizar" desvincula o template.
- Tela de criação de usuário: campo "Perfil" agora opcional (usuário livre).

---

### §2 — Painel Admin Global

**Nova tabela:** `platform_admins` (id, email, name, password_hash, is_active, created_at)

**Auth:**
- Endpoint: `POST /api/platform/auth/login`
- JWT: mesmo `JWT_SECRET`, claim `platform_admin: true`, sem `tenant_id`
- Middleware dedicado para rotas `/api/platform/*`: verificar `platform_admin: true` antes de qualquer handler
- Sem refresh token para platform admin na entrega inicial (sessão de backoffice, expiração padrão)

**Conexão de banco:**
- Nova variável de ambiente `DATABASE_URL_PLATFORM` apontando para role PostgreSQL com `BYPASSRLS`
- Engine e pool separados, nunca compartilhados com o app cliente
- Queries do painel usam exclusivamente esse engine

**Endpoints de entrega inicial:**
- `GET /api/platform/tenants` — lista com nome, CNPJ, status assinatura, data vencimento, filtro por status
- `GET /api/platform/tenants/{id}/users` — usuários do tenant com nome, username, perfil, último login
- `PATCH /api/platform/tenants/{id}/assinatura` — ativar/suspender (`status`: `ativa | suspensa`)

**KPIs:** fora do escopo desta entrega. Tabela `tenant_metrics_daily` planejada para §2.1.

---

### §3.X — Calendário de Eventos

**Nova tabela:** `tenant_eventos` (id, tenant_id, titulo, descricao, data_evento DATE, criado_por FK, created_at, updated_at)

**Índice:** `(tenant_id, data_evento)` para queries de mês.

**`data_evento`:** DATE sem timezone — capturado em horário local do servidor. Sem conversão de timezone (eventos são datas absolutas do calendário local).

**Endpoints:**
- `GET /api/eventos?mes=YYYY-MM` — lista eventos do mês corrente do tenant
- `POST /api/eventos` — criar evento
- `PATCH /api/eventos/{id}` — editar título e descrição
- `DELETE /api/eventos/{id}` — excluir

**Permissão:** nova tela `"calendario"` no catálogo de telas. Template Admin e Gerente recebem acesso; Caixa não.

**Front-end:** dois fluxos mapeiam para o mesmo endpoint POST. Clique na data pré-preenche e trava o campo de data no modal.

---

### §3.Y — Motor de Promoções

**Novas tabelas:**
- `promocoes`: campos de vigência (data_inicio, data_fim nullable, hora_inicio, hora_fim), recorrência (tipo_recorrencia ENUM, dias_semana INT[], dias_mes INT[]), desconto (tipo + valor), criado_por
- `promocao_produtos`: (promocao_id, produto_id) — PK composta

**Tipo ENUM:** `tipo_recorrencia` (`nenhuma`, `semanal`, `mensal`)

**Validação Pydantic (não no banco):**
- `recorrencia = 'nenhuma'` → `dias_semana = None`, `dias_mes = None`
- `recorrencia = 'semanal'` → `dias_semana` obrigatório e não-vazio
- `recorrencia = 'mensal'` → `dias_mes` obrigatório e não-vazio

**Engine de desconto no PDV:**
Verificação backend ao lançar item na comanda:
1. Buscar promoções ativas: `data_inicio <= hoje`, (`data_fim IS NULL OR data_fim >= hoje`), hora válida, recorrência satisfeita
2. Filtrar por `produto_id` na `promocao_produtos`
3. Se múltiplas promos: `ORDER BY id ASC LIMIT 1`
4. Aplicar desconto sobre `preco_venda` do produto

**Conflito de promoções:** first-wins por `id ASC`. Documentado na UI.

**Permissão:** tela `"promocoes"` (leitura) e separação de criação/edição dentro da mesma tela via perfil. Ou simplificado: mesma tela `"cadastros"` estendida — decisão final na implementação.

---

### §3.Z — Cockpit Consolidado

**View SQL `view_calendario_consolidado`:** UNION ALL de 4 camadas usando nomes reais de tabelas/colunas do codebase:
- Camada 1: `tenant_eventos` → tipo `evento`
- Camada 2: `promocoes` (vigentes) → tipo `promocao`
- Camada 3: `contas_pagar JOIN fornecedores` (status `pendente`) → tipo `conta_pagar`
- Camada 4: `compras JOIN fornecedores` (status `confirmado`, `data_prevista_recebimento NOT NULL`) → tipo `entrega_insumo`

**Colunas da view:** `(tenant_id, data_referencia DATE, tipo VARCHAR, referencia_id, descricao, hora_inicio TIME)`

**Endpoint:** `GET /api/calendario/consolidado?mes=YYYY-MM` — filtra camadas conforme permissões do usuário no JWT:
- `conta_pagar` exige telas `"calendario"` E `"financeiro"` (ou tela equivalente de contas)
- `entrega_insumo` exige telas `"calendario"` E `"estoque"`
- Omissão acontece em nível de API — front não recebe dados que o usuário não pode ver

**Front-end:** toggles de filtro por camada; deep link de cada card para tela de origem; popover de detalhe ao hover/click.

---

## Testing Decisions

**O que é um bom teste aqui:** testa comportamento externo observável — o que a API retorna dado um estado de banco específico. Não testa implementação interna (qual query foi executada, quais funções foram chamadas).

**Prior art no codebase:** ver `tests/` — testes de integração com banco real (SQLite em memória para testes, PostgreSQL em CI). Padrão: fixture cria tenant + usuário + perfil, chama endpoint via `TestClient`, asserta resposta HTTP e estado do banco.

**Módulos a testar com integração:**

| Módulo | O que testar |
|--------|-------------|
| §1 — Resolução de permissão | JWT com template retorna telas corretas; mudança de template reflete no refresh; usuário livre usa user_permissions |
| §1 — Migration | Perfis existentes acessíveis após migration; tokens V1 ainda válidos durante janela de transição |
| §2 — Auth platform admin | Login válido retorna JWT com `platform_admin: true`; rota `/api/platform/*` rejeita JWT de tenant; rejeita JWT sem claim |
| §2 — Isolamento BYPASSRLS | Query do painel retorna dados de múltiplos tenants; query de app cliente não vaza dados entre tenants |
| §3.X — Eventos | CRUD completo; query por mês retorna apenas eventos do tenant; RLS impede acesso cross-tenant |
| §3.Y — Engine de desconto | Item com promo ativa recebe desconto; item fora do horário não recebe; conflito de promos aplica a mais antiga; recorrência semanal/mensal respeitada |
| §3.Y — Validação Pydantic | `recorrencia=nenhuma` com `dias_semana` preenchido rejeitado; `semanal` sem `dias_semana` rejeitado |
| §3.Z — Filtro de camadas por permissão | Usuário sem tela `financeiro` não recebe camada `conta_pagar` na resposta; usuário com todas as telas recebe todas as camadas |

---

## Out of Scope

- **Permissões granulares por ação (ALLOW/DENY):** descartado para V2. Reavaliar quando clientes enterprise com requisitos de compliance chegarem. A base V1.5 permite migração incremental.
- **KPIs do Painel Admin (§2.1):** requisitos de negócio não definidos. Entregue como módulo separado após fechamento de requisitos.
- **Eventos recorrentes no Calendário:** `tenant_eventos` armazena datas únicas. Recorrência de eventos (não de promoções) fora do escopo.
- **Notificações push/email para eventos e contas a pagar:** infraestrutura de notificação não especificada.
- **Módulo de Planos e Precificação:** modelo comercial não definido.
- **Sub-receita (insumo composto), KDS, QR Code, NFC-e/SAT.**
- **Histórico de auditoria visual de `eventos_comanda`.**
- **Relatórios avançados de CMV/margem por prato.**

---

## Further Notes

- **Screens V1 existentes:** `cadastros`, `caixa`, `comandas`, `compras`, `configuracoes`, `consumo_interno`, `dashboard`, `estoque`, `relatorios`. Novas telas a adicionar: `calendario`, possivelmente `promocoes`.
- **`rotate_refresh_token` já recomputa permissões** do banco — a estratégia de 15min não exige nova infra, apenas reduzir `JWT_EXPIRES_MINUTES` no settings.
- **View §3.Z usa `compras.status = 'confirmado'`** para "entregas esperadas" — semanticamente: pedido confirmado com fornecedor, ainda não recebido no estoque. Validar com equipe se `status = 'recebido'` já significa entrada física.
- **`fornecedor_nome` na view:** resolvido via `LEFT JOIN fornecedores ON fornecedores.id = compras.fornecedor_id` — coluna real é `fornecedores.nome`.
- **Ordem de execução sugerida:** §1 → §2 → §3.X → §3.Y → §3.Z. Cada módulo é independente exceto §3.Y que depende de §3.X (calendário visual) e §3.Z que depende de §3.X e §3.Y.
