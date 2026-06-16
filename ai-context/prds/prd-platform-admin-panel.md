# PRD — Platform Admin Panel (Back-office Flow4Tech)

## Problem Statement

O painel administrativo interno da Flow4Tech (`/platform/*`) é rudimentar: exibe apenas uma tabela de tenants com nome fantasia e status de assinatura, sem identidade visual consistente com a aplicação principal e sem as ferramentas necessárias para o time de operações gerenciar o ciclo de vida completo de clientes (empresas). Hoje, qualquer ação além de ativar/suspender assinatura exige acesso direto ao banco de dados.

## Solution

Redesenho completo do painel de administração da plataforma Flow4Tech, com identidade visual idêntica à aplicação de tenant, cobrindo o ciclo de vida completo de cada empresa cliente: criação, configuração, gestão de usuários e perfis, controle de assinatura/trial, feature flags por módulo, cockpit de métricas, impersonation para suporte, log de auditoria e envio de comunicados.

## User Stories

### Identidade Visual e Navegação

1. Como admin da plataforma, quero que o painel tenha sidebar e estilo visual idênticos à aplicação de tenant, para não sentir que estou usando um sistema completamente diferente.
2. Como admin, quero navegar entre seções pelo menu lateral (Empresas, Cockpit, Comunicados, Auditoria), para acessar qualquer área com um clique.
3. Como admin, quero ver meu e-mail e um botão de logout no topo, para saber com qual conta estou autenticado.

### Gestão de Empresas (Tenants)

4. Como admin, quero ver a lista de empresas com colunas: ID, Nome Fantasia, CNPJ, Status Tenant, Status Assinatura, Vencimento e Qtd Usuários (atual/máximo), para ter uma visão completa de cada cliente.
5. Como admin, quero filtrar a lista por status de assinatura (trial, ativa, suspensa, cancelada), para focar nos casos que precisam de atenção.
6. Como admin, quero criar uma nova empresa informando nome fantasia, CNPJ, endereço, telefone e limite máximo de usuários, para onboarding de novos clientes sem acessar o banco diretamente.
7. Como admin, quero que toda empresa criada comece com assinatura `trial` automaticamente, para padronizar o processo de entrada.
8. Como admin, quero configurar uma duração padrão global para trials (ex: 14 dias), para que todos os novos tenants sigam o mesmo prazo por padrão.
9. Como admin, quero sobrescrever a duração do trial individualmente ao criar ou editar um tenant, para casos especiais (parceiros, pilotos).
10. Como admin, quero clicar em uma empresa e acessar a página de detalhe com abas: Dados, Usuários e Perfis, para gerenciar tudo em um lugar.

### Aba Dados (Detalhe do Tenant)

11. Como admin, quero editar nome fantasia, CNPJ, endereço, telefone e limite máximo de usuários de qualquer tenant, para manter os dados atualizados.
12. Como admin, quero ver o ID interno, data de criação e status atual do tenant como campos read-only, para referência rápida.
13. Como admin, quero alterar o status da assinatura (trial / ativa / suspensa / cancelada) com um seletor, para controlar o acesso do cliente sem precisar de ferramenta externa.
14. Como admin, quero definir a data de vencimento da assinatura manualmente, para casos de pagamento manual ou extensão de prazo.
15. Como admin, quero ver o histórico de mudanças de status da assinatura (data, status anterior, status novo, quem alterou), para ter rastreabilidade do ciclo de vida de cada cliente.

### Bloqueio por Status de Assinatura

16. Como usuário de um tenant com assinatura vencida ou suspensa, quero ver uma tela de bloqueio clara ao logar, informando o motivo e contato para regularização, para entender o que aconteceu sem ficar preso em estado indefinido.
17. Como admin, quero que tenants bloqueados possam logar mas vejam apenas a tela de bloqueio, sem acesso a nenhum módulo funcional.

### Aba Usuários

18. Como admin, quero ver todos os usuários de um tenant com: nome, username, e-mail, perfil, último login e status ativo/inativo.
19. Como admin, quero criar um novo usuário em qualquer tenant informando nome, username, e-mail, senha e perfil, sem precisar acessar as configurações do tenant.
20. Como admin, quero editar nome, username, e-mail, perfil e status de qualquer usuário de qualquer tenant.
21. Como admin, quero redefinir a senha de qualquer usuário diretamente, para suporte a clientes bloqueados.
22. Como admin, quero ativar ou desativar um usuário com um clique, para controle de acesso imediato.
23. Como admin, quero ver o indicador "X / max_users usuários ativos" na aba, para saber se o tenant está no limite.
24. Como admin, quero alterar o limite máximo de usuários do tenant diretamente na aba, para ajustes de plano rápidos.

### Aba Perfis e Permissões

25. Como admin, quero ver todos os perfis de um tenant com nome, descrição, lista de permissões e quantidade de usuários vinculados.
26. Como admin, quero editar as permissões de um perfil via checkboxes por módulo (dashboard, calendário, comandas, consumo interno, compras, estoque, relatórios, cadastros, configurações, gestão de usuários, financeiro/contas a pagar), para ajustar o que cada grupo de usuários pode acessar.
27. Como admin, quero ativar ou desativar um perfil, para bloquear um grupo sem excluí-lo.

### Feature Flags por Tenant

28. Como admin, quero habilitar ou desabilitar módulos individualmente por tenant (dashboard, calendário, comandas, consumo interno, compras/NF-e, estoque, relatórios, cadastros, configurações, gestão de usuários, financeiro), para controlar quais funcionalidades estão disponíveis conforme o plano contratado.
29. Como admin, quero que módulos desabilitados não apareçam no menu lateral do tenant e que os endpoints correspondentes retornem 403, para consistência entre UI e API.
30. Como admin, quero ver o estado atual de todos os feature flags de um tenant numa tela dedicada dentro do detalhe, para ter visibilidade imediata.

### Impersonation (Entrar como Tenant)

31. Como admin, quero clicar em "Entrar como" em qualquer usuário de um tenant e ser redirecionado para a aplicação como se fosse aquele usuário, para suporte e debugging sem pedir senha ao cliente.
32. Como admin, quero que a sessão de impersonation seja marcada visualmente na UI do tenant (ex: banner "Sessão de suporte ativa — admin@flow4tech.com"), para nunca confundir a sessão real com a de suporte.
33. Como admin, quero que todas as ações realizadas durante impersonation sejam registradas no log de auditoria com flag `impersonated_by`, para rastreabilidade completa.
34. Como admin, quero poder encerrar a sessão de impersonation e voltar ao painel de admin com um clique no banner.
35. Como admin, quero que tokens de impersonation tenham TTL curto (ex: 2 horas), para reduzir risco de vazamento.

### Cockpit de Métricas

36. Como admin, quero ver um cockpit geral com cards por tenant mostrando: último login, comandas no mês, faturamento estimado do mês, usuários ativos nos últimos 30 dias, compras/NF-e registradas no mês e dias como cliente.
37. Como admin, quero poder ordenar a lista do cockpit por qualquer métrica, para identificar os clientes mais/menos ativos.
38. Como admin, quero filtrar o cockpit por status de assinatura, para monitorar especificamente trials próximos do vencimento.
39. Como admin, quero ver dentro do detalhe de cada tenant um painel de métricas consolidado com os mesmos dados do cockpit geral, para contexto ao fazer suporte.

### Comunicados

40. Como admin, quero criar um comunicado com título, mensagem e data de expiração, para informar clientes sobre manutenções, novidades ou alertas.
41. Como admin, quero enviar um comunicado para todos os tenants ativos (broadcast) ou selecionar tenants específicos, para comunicação direcionada.
42. Como usuário de tenant, quero ver comunicados ativos em um banner no topo da aplicação, para ser informado de avisos importantes da plataforma.
43. Como usuário de tenant, quero poder fechar/marcar como lido um comunicado, para não vê-lo repetidamente após tomar ciência.
44. Como admin, quero ver quantos tenants/usuários já viram cada comunicado, para medir o alcance.

### Log de Auditoria

45. Como admin, quero ver um log de auditoria global com todas as ações relevantes do sistema: ações de admins da plataforma, criação/edição/exclusão feitas por usuários dos tenants e ações durante impersonation.
46. Como admin, quero filtrar o log por tenant, por usuário, por tipo de ação e por período, para investigações pontuais.
47. Como admin, quero que cada entrada do log contenha: timestamp, tenant, usuário, ação, entidade afetada, valores anteriores e novos (quando aplicável) e flag de impersonation.

## Implementation Decisions

### Novos Endpoints Backend (`/api/platform/`)

**Tenants:**
- `POST /tenants` — criar tenant + assinatura trial
- `GET /tenants/:id` — detalhe completo
- `PATCH /tenants/:id` — atualizar dados e max_users
- `GET /tenants/:id/assinatura/historico` — histórico de mudanças

**Usuários do tenant:**
- `POST /tenants/:id/users` — criar usuário
- `PATCH /tenants/:id/users/:uid` — editar (nome, email, username, senha opcional, perfil, is_active)

**Perfis do tenant:**
- `GET /tenants/:id/profiles` — listar com permissões
- `PATCH /tenants/:id/profiles/:pid` — atualizar permissões + is_active

**Feature flags:**
- `GET /tenants/:id/features` — estado atual de todos os flags
- `PUT /tenants/:id/features` — substituir todos os flags de uma vez

**Assinatura:**
- `PATCH /tenants/:id/assinatura` — já existe, expandir com `data_vencimento`
- `GET /tenants/:id/assinatura/historico`

**Impersonation:**
- `POST /tenants/:id/users/:uid/impersonate` — retorna JWT de impersonation (TTL 2h, campo `impersonated_by` no payload)

**Cockpit:**
- `GET /cockpit` — métricas agregadas de todos os tenants
- `GET /tenants/:id/cockpit` — métricas de um tenant específico

**Comunicados:**
- `GET /announcements` — listar
- `POST /announcements` — criar
- `PATCH /announcements/:id` — editar/desativar
- `GET /app/announcements` — endpoint público (autenticado como tenant user) para buscar comunicados ativos para o seu tenant
- `POST /app/announcements/:id/read` — marcar como lido

**Auditoria:**
- `GET /audit-logs` — com filtros: tenant_id, user_id, action, date_from, date_to

**Configurações globais:**
- `GET /settings` — buscar config global (ex: `trial_duration_days`)
- `PATCH /settings` — atualizar config global

### Novos Modelos / Tabelas

| Tabela | Propósito |
|--------|-----------|
| `tenant_features` | `tenant_id`, `feature`, `enabled` — feature flags por tenant |
| `platform_announcements` | `title`, `body`, `expires_at`, `created_by`, `target` (all/specific) |
| `announcement_targets` | `announcement_id`, `tenant_id` — tenants-alvo de comunicados direcionados |
| `announcement_reads` | `announcement_id`, `user_id`, `read_at` |
| `audit_logs` | `tenant_id`, `user_id`, `action`, `entity`, `entity_id`, `before`, `after`, `impersonated_by`, `created_at` |
| `platform_settings` | `key`, `value` — configurações globais (ex: `trial_duration_days = 14`) |
| `assinatura_history` | `assinatura_id`, `from_status`, `to_status`, `changed_by`, `created_at` |

### Bloqueio de Assinatura

Middleware no backend (dependência FastAPI) que em cada request autenticado de tenant verifica `assinaturas.status` e `data_vencimento`. Se suspenso/cancelado/vencido, retorna `HTTP 402` com código de erro `SUBSCRIPTION_BLOCKED`. Frontend intercepta 402 e redireciona para tela de bloqueio.

### Feature Flags

Dependência FastAPI `require_feature(screen)` injeta verificação de `tenant_features` antes de cada endpoint de módulo. Frontend usa endpoint `GET /app/features` para buscar flags ativos e ocultar itens do menu lateral dinamicamente.

### Impersonation

Token JWT com claims extras: `impersonated_by: <platform_admin_id>`, `impersonation: true`. Middleware de audit log verifica presença desse campo e registra automaticamente. TTL fixo de 2 horas, não renovável via refresh token.

### Cockpit

Queries SQL diretas em `information_schema` ou views agregadas. Não criar ORM complexo — usar raw SQL no `platform_repository`. Dados podem ser levemente defasados (sem cache por ora, query on-demand).

### Comunicados

Tabela `platform_announcements` com `target = 'all' | 'specific'`. Endpoint do app (`/api/app/announcements`) filtra por tenant_id e `expires_at > now()` e `not in announcement_reads` para o usuário. Banner no `Topbar.tsx` existente.

### Audit Log

Service `audit_service.log(db, action, entity, entity_id, before, after, user_id, tenant_id, impersonated_by)` chamado explicitamente nos services críticos. Não usar triggers de banco para manter lógica no Python e facilitar testes.

## Testing Decisions

Bons testes verificam comportamento externo (response HTTP, estado do banco), não implementação interna.

**Módulos a testar:**

- **Bloqueio de assinatura** — tenant com status `suspensa` recebe 402 em qualquer endpoint protegido; tenant `ativa` passa normalmente.
- **Feature flags** — endpoint de módulo desabilitado retorna 403; habilitado retorna normalmente.
- **Impersonation** — token gerado funciona como o usuário-alvo; ação registrada em audit_log com `impersonated_by`; token expirado em 2h.
- **Comunicados** — usuário de tenant específico não vê comunicado de outro tenant; comunicado expirado não aparece; marcar como lido oculta nas próximas chamadas.
- **Cockpit** — métricas retornam valores corretos para tenant com dados conhecidos (fixture).

Prior art de testes: `tests/test_platform_auth.py`, `tests/test_auth.py`, `tests/conftest.py`.

## Out of Scope

- Integração com gateway de pagamento (Stripe, PagSeguro) — gestão de assinatura é manual por enquanto
- Envio de e-mail automático ao vencer trial
- App mobile para admins
- Permissões granulares dentro do painel de admin (todos os admins têm acesso total ao painel)
- Editor visual de e-mail para comunicados
- Multi-tenancy do próprio painel de admin (não há sub-admins com escopos limitados)
- Backup/restore de dados por tenant

## Further Notes

- `platform_settings` deve ter uma entrada inicial: `trial_duration_days = 14`
- A tela de bloqueio deve exibir e-mail de contato configurável via `platform_settings`
- O banner de impersonation deve ser injetado no `Topbar.tsx` verificando o campo `impersonation` no JWT decodificado do store de auth
- Feature flags e permissões de perfil são camadas independentes: flags controlam acesso ao módulo inteiro; permissões de perfil controlam acesso dentro do módulo para usuários específicos
- Audit log de ações de tenant deve ser assíncrono (fire-and-forget) para não impactar latência das operações normais — usar `BackgroundTasks` do FastAPI
