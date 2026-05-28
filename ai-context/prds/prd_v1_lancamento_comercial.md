# PRD — Flow4Food V1: Lançamento Comercial

**Produto:** Flow4Food (produto da Flow4Tech)
**Escopo:** Tudo que falta implementar para a V1 ser comercialmente viável como SaaS multi-tenant.
**Decisões fixadas:**
- Um banco de dados único (PostgreSQL no Railway) — sem sharding
- Onboarding manual: admin Flow4Tech cria tenants via painel interno ou script
- Billing manual: sem gateway de pagamento na V1 (admin registra pagamento diretamente)
- Nova tela `caixa` no universo de permissões

---

## Problem Statement

O sistema Flow4Food (ex-Matchpoint) existe como protótipo funcional single-tenant: gerencia comandas, estoque, compras e relatórios para um único estabelecimento com TENANT_ID = 1 hardcoded em serviços de autenticação e usuários. Para ser comercializado como SaaS, precisa de cinco evoluções críticas:

1. **Multi-tenancy** — hoje todos os dados pertencem implicitamente a um tenant fictício. Não há isolamento real entre empresas, impossibilitando hospedar múltiplos clientes no mesmo banco.
2. **Controle de assinatura** — não existe mecanismo para bloquear/liberar acesso por empresa conforme situação financeira, essencial para viabilidade comercial.
3. **Auditoria de caixa** — donos precisam abrir/fechar o caixa do dia e conciliar o dinheiro físico com o registrado no sistema. Hoje esse controle não existe.
4. **Bugs de concorrência** — dois lançamentos simultâneos do mesmo insumo provocam lost update silencioso no estoque; `aplicar_desconto` e `cancelar_comanda` escrevem sem passar pelo CAS de versão.
5. **Rebranding** — o nome "Matchpoint" ainda aparece na interface e na API. O produto precisa ser identificado como Flow4Food, da Flow4Tech.

---

## Solution

Transformar o sistema num SaaS multi-tenant real através de:

- **Tabela `tenants`** que substitui o singleton `estabelecimento`, com isolamento garantido por Row-Level Security (RLS) nativo do PostgreSQL — isolamento é garantia do banco, não disciplina do desenvolvedor.
- **`tenant_id` em todas as tabelas operacionais** e injeção automática via `SET app.tenant_id` na sessão do banco, lido exclusivamente do JWT assinado.
- **Sistema de assinaturas** (`planos`, `assinaturas`, `pagamentos_assinatura`) com máquina de estados trial → ativa → vencida/cancelada/suspensa. Controle de acesso em dois níveis: JWT (baixo custo) + banco (autoritativo no refresh). Bloqueio de empresa = 1 UPDATE, sem tocar usuários.
- **Auditoria de caixa** (`caixa_sessoes`, `caixa_movimentos`) com abertura, fechamento com diferença calculada vs. informada, sangria e suprimento.
- **Correção de concorrência**: `SELECT ... FOR UPDATE` no fluxo de reserva de estoque da comanda; padronizar `increment_version` em todas as mutações de comanda.
- **Rebranding** de todas as referências Matchpoint → Flow4Food/Flow4Tech.

---

## User Stories

### Multi-tenancy e Onboarding

1. Como admin da Flow4Tech, quero criar um novo tenant (empresa cliente) via painel interno, para que ela passe a existir isolada no sistema sem interferir em outros clientes.
2. Como admin da Flow4Tech, quero que ao criar um tenant seus perfis padrão (Admin, Gerente, Caixa) sejam clonados automaticamente e vinculados a ele, para que ele já nasça com permissões funcionais sem configuração manual.
3. Como admin da Flow4Tech, quero que a criação de tenant, clone de perfis e primeiro usuário admin ocorram numa transação atômica, para que não existam tenants sem dono nem usuários sem perfil em caso de falha.
4. Como admin da Flow4Tech, quero que cada tenant tenha seu `admin_user_id` registrado, para que eu saiba quem é o responsável financeiro de cada empresa.
5. Como admin da Flow4Tech, quero que o e-mail do usuário admin seja obrigatório durante o onboarding, para que ele receba notificações de billing e recuperação de senha.
6. Como dono de restaurante (usuário Admin), quero criar funcionários (Garçom, Gerente, Caixa) dentro da minha empresa, para que eles acessem apenas os dados do meu estabelecimento.
7. Como dono de restaurante, quero que o `tenant_id` dos funcionários que crio seja herdado automaticamente do meu JWT, para que seja impossível criar um usuário acidentalmente em outra empresa.
8. Como funcionário (e-mail opcional), quero fazer login com username + senha, para que mesmo sem e-mail eu consiga acessar o sistema.
9. Como qualquer usuário, quero que o JWT contenha `tenant_id`, `permissions` e `subscription_status`, para que o sistema tome decisões de acesso sem consultar o banco a cada request.
10. Como dono de restaurante, quero que os dados do meu estabelecimento (comandas, insumos, produtos, estoque, compras, pagamentos) sejam isolados dos demais clientes a nível de banco de dados, para que haja garantia técnica de que um bug de código não exponha dados de outra empresa.

### Controle de Acesso e Assinaturas

11. Como admin da Flow4Tech, quero suspender instantaneamente o acesso de uma empresa inadimplente com 1 UPDATE na tabela `assinaturas`, para que não precise alterar registros de usuários individualmente.
12. Como admin da Flow4Tech, quero reativar uma empresa após pagamento com 1 UPDATE e nova `data_vencimento`, para que o acesso seja restaurado rapidamente.
13. Como admin da Flow4Tech, quero que um job diário marque como `vencida` toda assinatura cujo `data_vencimento` passou sem pagamento, para que o bloqueio seja automático sem intervenção manual.
14. Como admin da Flow4Tech, quero registrar manualmente um pagamento em `pagamentos_assinatura` com `gateway_ref` opcional, para que haja histórico de conciliação financeira.
15. Como admin da Flow4Tech, quero criar e editar planos (`planos`) com preço e limites, para que diferentes empresas possam ser enquadradas em tiers de serviço.
16. Como novo tenant, quero começar num período de trial com acesso liberado, para que possa avaliar o sistema antes de pagar.
17. Como dono de restaurante (Admin) em empresa suspensa, quero ver uma tela explicando que a assinatura está vencida com instruções de regularização, para que eu saiba o que fazer para recuperar o acesso.
18. Como funcionário (Garçom/Caixa/Gerente) em empresa suspensa, quero ver uma mensagem direta dizendo que a conta está suspensa e devo procurar o responsável, para que eu entenda a situação sem receber informações de billing que não são da minha responsabilidade.
19. Como qualquer usuário, quero que ao renovar o access token o `subscription_status` seja relido do banco, para que uma suspensão administrativa propague para todos os funcionários no próximo refresh sem precisar invalidar sessões individuais.
20. Como admin da Flow4Tech, quero poder revogar todos os refresh tokens de um tenant em caso crítico, para que o bloqueio seja imediato sem esperar o TTL do access token.

### Auditoria de Caixa

21. Como operador de caixa, quero abrir uma sessão de caixa informando o fundo de troco inicial, para que o sistema saiba qual valor monetário estava disponível no início do turno.
22. Como operador de caixa, quero que o sistema impeça abertura de uma segunda sessão enquanto uma já estiver aberta, para que não haja sobreposição de turnos no mesmo tenant.
23. Como operador de caixa, quero registrar uma sangria (retirada de dinheiro) durante o turno com valor e motivo, para que movimentações manuais estejam documentadas.
24. Como operador de caixa, quero registrar um suprimento (aporte de dinheiro) durante o turno com valor e motivo, para que reforços de troco sejam rastreados.
25. Como operador de caixa, quero fechar o caixa informando o valor contado na gaveta, para que o sistema calcule automaticamente a diferença entre o esperado e o real.
26. Como dono de restaurante, quero que o valor calculado no fechamento derive de `pagamentos em dinheiro` + `suprimentos` - `sangrias` + `fundo de troco`, para que o cálculo seja auditável a partir de dados já registrados.
27. Como dono de restaurante, quero visualizar a diferença (quebra ou sobra) ao fechar o caixa, para que eu possa identificar inconsistências no caixa físico.
28. Como dono de restaurante, quero que a permissão de abrir/fechar caixa esteja numa tela `caixa` separada, para que eu possa dar esse acesso ao Caixa sem necessariamente dar acesso à gestão completa de comandas.
29. Como operador de caixa, quero poder adicionar uma observação ao fechar o caixa, para que eu documente eventos anômalos do turno.
30. Como dono de restaurante, quero que os dados de caixa sejam isolados por tenant via RLS, para que sessões de outras empresas não sejam visíveis.

### Correção de Concorrência

31. Como sistema, quero que a reserva de estoque na comanda use `SELECT ... FOR UPDATE`, para que dois lançamentos simultâneos do mesmo insumo não causem lost update silencioso.
32. Como sistema, quero que `aplicar_desconto` na comanda passe pelo CAS de versão (`increment_version`), para que não haja lost update ao aplicar desconto concorrentemente.
33. Como sistema, quero que `cancelar_comanda` passe pelo CAS de versão, para que o cancelamento concorrente não corrompa o estado da comanda.
34. Como sistema, quero que nenhuma mutação de comanda ocorra sem CAS de versão, para que o modelo de edição colaborativa seja consistente.

### Rebranding

35. Como usuário final, quero ver "Flow4Food" no título do navegador e na interface do sistema, para que a identidade do produto seja clara.
36. Como usuário final, quero ver a relação "Flow4Food — um produto Flow4Tech" no card de login e no rodapé, para que a marca mãe esteja visível.
37. Como desenvolvedor integrando a API, quero que o título da API seja "Flow4Food API", para que documentação e swagger reflitam o produto correto.
38. Como usuário que recebe e-mail de reset de senha, quero que o assunto e corpo do e-mail referenciem Flow4Food/Flow4Tech, para que a identidade da marca seja coerente em todos os pontos de contato.

---

## Implementation Decisions

### Módulos a construir / modificar

**1. TenantRepository + TenantService**
- Operações: `create_tenant`, `get_tenant_by_id`, `update_tenant_status`
- Responsável pelo fluxo atômico de onboarding: INSERT tenants → clone profiles → INSERT system_users → UPDATE admin_user_id → INSERT assinaturas (tudo numa transação)
- Clone de perfis usa o seed `0035_seed_default_profiles.py` como molde

**2. Migrations RLS (novo bloco de migrations alembic)**
- Tabela `tenants` (substitui `estabelecimento` como entidade de empresa)
- `tenant_id NOT NULL` em: `comandas`, `itens_comanda`, `insumos`, `produtos`, `movimentos_estoque`, `compras`, `pagamentos`, `comissoes_garcom`, `eventos_comanda`, `categorias`, `fornecedores`, `profiles`, `profile_permissions`, `system_users`
- Índices compostos com `tenant_id` como primeira coluna
- `ENABLE ROW LEVEL SECURITY` + `CREATE POLICY tenant_isolation` em todas as tabelas acima
- Role PostgreSQL sem `BYPASSRLS` para a aplicação (configuração de infra)

**3. DatabaseSession (get_db)**
- `SET app.tenant_id = :tid` injetado a partir do claim `tenant_id` do JWT **antes** de qualquer query
- `tenant_id` lido exclusivamente do JWT assinado — nunca de header HTTP ou body de request

**4. AuthService / JWT**
- Claims obrigatórios adicionados: `tenant_id` (int), `subscription_status` (str)
- No refresh do token: reler `assinaturas.status` do banco e reemitir access token com valor atual
- TENANT_ID = 1 hardcoded removido de `users_service`, `profiles_service`, `auth_service`

**5. SubscriptionService + BillingRepository**
- Tabelas: `planos`, `assinaturas`, `pagamentos_assinatura`
- `require_active_subscription` dependency: 402 se `subscription_status` ∉ {ativo, trial}
- Job diário no scheduler existente: marca `vencida` toda assinatura cujo `data_vencimento < CURRENT_DATE`
- Operações admin: criar plano, registrar pagamento, suspender/reativar tenant

**6. CaixaService + CaixaRepository**
- Tabelas: `caixa_sessoes`, `caixa_movimentos` (ambas com `tenant_id` + RLS)
- Operações: `abrir_caixa`, `fechar_caixa`, `registrar_sangria`, `registrar_suprimento`, `get_sessao_aberta`
- Índice único parcial: apenas uma sessão aberta por tenant
- Cálculo de fechamento: `valor_abertura + SUM(pagamentos em dinheiro na janela) + SUM(suprimentos) - SUM(sangrias)`
- Permissão: `require_permission("caixa")` — nova tela adicionada ao universo de permissões

**7. Correção de concorrência (ComandasService + EstoqueRepository)**
- `_reservar_estoque` e `_baixar_insumo`: trocar SELECT simples por `estoque_repository.get_insumo_for_update`
- `aplicar_desconto` e `cancelar_comanda`: passar por `increment_version` (CAS de versão)

**8. Frontend — SubscriptionGuard**
- Interceptor HTTP trata 402 diferentemente por perfil (lido do JWT)
- Admin → tela "Assinatura Vencida" com instruções de pagamento e contato Flow4Tech
- Demais perfis → modal/tela "Conta suspensa — procure o responsável"

**9. Frontend — Tela de Caixa**
- Feature nova em `/features/caixa/`
- Fluxos: abertura de sessão, registro de sangria/suprimento, fechamento com inserção do valor contado
- Exibe valor calculado, valor informado, diferença ao fechar

**10. Rebranding**
- `frontend/index.html`: `<title>Flow4Food</title>`
- `frontend/src/features/auth/LoginPage.tsx`: logo + "por Flow4Tech"
- `frontend/src/components/layout/Topbar.tsx`: marca Flow4Food
- `frontend/src/features/auth/EsqueciSenhaPage.tsx` e `RedefinirSenhaPage.tsx`: marca atualizada
- `frontend/src/pages/PlaceholderPage.tsx`: marca atualizada
- `backend/src/main.py`: `title="Flow4Food API"`
- `backend/src/services/auth_service.py`: assunto do e-mail atualizado

### Schema changes resumido

```
tenants                  — nova (substitui singleton estabelecimento)
planos                   — nova
assinaturas              — nova (1 por tenant, status: trial/ativa/vencida/cancelada/suspensa)
pagamentos_assinatura    — nova (append-only, histórico financeiro)
caixa_sessoes            — nova (1 aberta por tenant, índice único parcial)
caixa_movimentos         — nova (sangria/suprimento, append-only)

[todas as tabelas operacionais] += tenant_id BIGINT NOT NULL + RLS policy
system_users             += tenant_id NOT NULL, UNIQUE(email) when NOT NULL
profiles                 += tenant_id NOT NULL + RLS
profile_permissions      += tenant_id NOT NULL + RLS
```

### API contracts (novos endpoints)

- `POST /admin/tenants` — cria tenant + onboarding atômico (restrito a superadmin Flow4Tech)
- `GET/PATCH /admin/tenants/{id}` — leitura e gestão de tenant
- `POST /admin/tenants/{id}/payments` — registrar pagamento manual
- `PATCH /admin/tenants/{id}/subscription` — suspender/reativar
- `GET /admin/plans` / `POST /admin/plans` — catálogo de planos
- `GET /caixa/sessao` — sessão aberta do tenant atual
- `POST /caixa/abrir` — abre sessão com fundo de troco
- `POST /caixa/fechar` — fecha com valor informado
- `POST /caixa/movimentos` — registra sangria ou suprimento

---

## Testing Decisions

**O que é um bom teste aqui:**
- Testa comportamento externo (o que a API/serviço retorna), não implementação interna
- Não mocka o banco de dados — os bugs mais críticos aqui (RLS, FOR UPDATE, CAS de versão) só aparecem com banco real
- Usa transações de teste que fazem rollback ao final para isolamento entre testes

**Módulos que precisam de testes:**

| Módulo | O que testar |
|---|---|
| RLS / tenant isolation | Request de um tenant não retorna dados de outro; SET app.tenant_id ausente bloqueia acesso |
| TenantService onboarding | Transação atômica: falha no passo N faz rollback completo (sem tenant órfão) |
| AuthService JWT | Claims tenant_id e subscription_status presentes no token; refresh relê status do banco |
| SubscriptionService 402 | Token com status vencida retorna 402 em rota de negócio; status ativo passa |
| Job de vencimento | Assinatura com data_vencimento = ontem muda de ativa → vencida após rodar o job |
| CaixaService abertura | Segunda abertura no mesmo tenant enquanto há sessão aberta retorna erro |
| CaixaService fechamento | Diferença calculada = valor_abertura + pagamentos_dinheiro + suprimentos - sangrias |
| EstoqueRepository FOR UPDATE | Dois lançamentos simultâneos do mesmo insumo não causam lost update (teste com threads) |
| ComandasService CAS | aplicar_desconto e cancelar_comanda com versão desatualizada retornam 409 |

**Prior art no projeto:**
- `backend/src/repositories/estoque_repository.py` já tem `get_insumo_for_update` com SELECT FOR UPDATE — modelo para os novos testes de concorrência
- `backend/src/repositories/comandas_repository.py:73` (`increment_version`) — padrão CAS já testável como referência

---

## Out of Scope

- **Gateway de pagamento** (Stripe/Asaas/Pix) — V1 é billing manual; integração fica para V2
- **Self-service de onboarding** — cadastro de empresa via página pública fica para V2
- **Catálogo dinâmico de permissões** — V1 mantém perfis fixos (Admin/Gerente/Caixa) por tenant
- **Sub-receita** (insumo composto de outro insumo) — V2
- **Tela visual de auditoria de eventos_comanda** — V1 mantém apenas o registro bruto
- **Roteamento de impressão por setor** (bar/cozinha), **KDS avançado**, **Cardápio QR Code**, **NFC-e/SAT fiscal**
- **Migração de dados de protótipo** — banco comercial começa limpo; dados de teste não são migrados

---

## Further Notes

- **Ordem de implementação importa:** passos 1–3 (tenants, RLS, system_users) são refactor estrutural que toca todas as queries. Quanto mais código acumular antes de fazer, mais caro fica. Priorizar.
- **Role PostgreSQL:** a aplicação deve conectar com role sem `BYPASSRLS`; caso contrário todo o isolamento RLS é nulo. Isso é configuração de infra (Railway env vars), não de código.
- **TTL do access token:** deve ser ≤ 15 minutos para que uma suspensão administrativa propague rapidamente sem precisar revogar refresh tokens individualmente.
- **`estabelecimento` (singleton):** após migrar para `tenants`, o model e tabela `estabelecimento` podem ser deprecados. Configurações por tenant (nome fantasia, etc.) passam a viver em `tenants`.
- **Perfis padrão por tenant:** cada tenant nasce com sua cópia isolada de Admin/Gerente/Caixa + permissões de tela, clonada do seed `0035_seed_default_profiles.py`. O admin do tenant pode renomear ou ajustar permissões da sua cópia sem afetar outros tenants.
- **Ordem recomendada de implementação (do doc de arquitetura):**
  1. Tabela `tenants`
  2. `tenant_id` + RLS em tabelas operacionais + `profiles` + `profile_permissions` + injeção `get_db`
  3. `system_users.tenant_id` + UNIQUE email + onboarding atômico
  4. JWT com `tenant_id`/`subscription_status` + tratamento 402 no frontend
  5. Tabelas de billing + `require_active_subscription` + job de vencimento
  6. Auditoria de caixa
  7. (Paralelo ao passo 2) Correção de concorrência: FOR UPDATE no estoque + CAS em todas as mutações de comanda
  8. Rebranding
