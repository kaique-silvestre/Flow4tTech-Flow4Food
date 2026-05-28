# Issues — Flow4Food V1: Lançamento Comercial

**Parent PRD:** `ai-context/prds/prd_v1_lancamento_comercial.md`
**Gerado em:** 2026-05-28.

9 fatias verticais (schema → API → frontend → testes). Issues 8 e 9 são independentes e podem começar imediatamente. Após Issue 1 aterrar: Issues 3 e 7 rodam em paralelo.

---

## Visão geral — grafo de dependências

```
Issue 8 (Rebranding) ────────────────────────────────────────────── (independente)

Issue 1 (RLS migrations) ──► Issue 3 (Onboarding) ──► Issue 4 (JWT) ──► Issue 5 (Billing) ──► Issue 6 (SubscriptionGuard)
                         └──► Issue 7 (Caixa backend) ──► Issue 9 (Caixa frontend)

Issue 2 (get_db + concorrência) ─── bloqueado por Issue 1 ─────────── (pode mergear junto)
```

---

## Issue 1 — RLS migrations foundation

**Type:** HITL
**Blocked by:** None — pode começar imediatamente.

### What to build

Criar a tabela `tenants` que substitui o singleton `estabelecimento` como entidade de empresa. Adicionar `tenant_id BIGINT NOT NULL` em todas as tabelas operacionais. Habilitar Row-Level Security (RLS) com policy `tenant_isolation` em cada tabela. Criar índices compostos com `tenant_id` como primeira coluna.

Tabelas que recebem `tenant_id` + RLS: `comandas`, `itens_comanda`, `insumos`, `produtos`, `movimentos_estoque`, `compras`, `pagamentos`, `comissoes_garcom`, `eventos_comanda`, `categorias`, `fornecedores`, `profiles`, `profile_permissions`, `system_users`.

**Ponto de atenção de infra (HITL):** a aplicação deve conectar com role PostgreSQL sem `BYPASSRLS`. Essa configuração é feita via env vars do Railway — se a role tiver `BYPASSRLS`, todo o isolamento é nulo. Requer confirmação de infra antes do deploy em produção.

### Acceptance criteria

- [ ] Migration `tenants` criada: `id`, `nome_fantasia`, `cnpj`, `status`, `admin_user_id`, `created_at`.
- [ ] `tenant_id NOT NULL` adicionado a todas as tabelas operacionais listadas acima via migration Alembic.
- [ ] `ENABLE ROW LEVEL SECURITY` + `CREATE POLICY tenant_isolation` (usando `current_setting('app.tenant_id')`) em cada tabela.
- [ ] Índices compostos `(tenant_id, id)` e `(tenant_id, <campo_busca>)` criados para as tabelas de alta leitura.
- [ ] `system_users.email` permite NULL; quando preenchido, `UNIQUE` se aplica (email opcional para funcionários).
- [ ] Teste de isolamento RLS: query com `app.tenant_id = 1` não retorna registros de tenant 2.
- [ ] Teste de bloqueio: query sem `SET app.tenant_id` retorna 0 linhas (RLS ativo).
- [ ] Migrations rodam do zero sem erro (`alembic upgrade head` em banco limpo).

### Blocked by

None — pode começar imediatamente.

### User stories addressed

- User story 1: tenant existe como entidade isolada no sistema
- User story 6: funcionários de um tenant não enxergam dados de outro
- User story 7: `tenant_id` herdado estruturalmente, impossível criar usuário em outra empresa
- User story 10: isolamento garantido pelo banco, não por disciplina do desenvolvedor

---

## Issue 2 — get_db injection + correção de concorrência

**Type:** AFK
**Blocked by:** Issue 1

### What to build

Dois trabalhos acoplados que tocam os mesmos arquivos de serviço e repositório:

**get_db injection:** modificar `get_db` (ou equivalente de sessão) para executar `SET app.tenant_id = :tid` — lendo o claim `tenant_id` do JWT assinado — antes de qualquer query. O `tenant_id` nunca vem de header HTTP ou body de request, apenas do JWT.

**Correção de concorrência:** substituir SELECTs simples por `SELECT FOR UPDATE` nos fluxos de reserva de estoque. Garantir que `aplicar_desconto` e `cancelar_comanda` passem pelo CAS de versão (`increment_version`). Nenhuma mutação de comanda deve ocorrer sem CAS.

### Acceptance criteria

- [ ] `get_db` executa `SET app.tenant_id = :tid` derivado exclusivamente do claim `tenant_id` do JWT antes de qualquer query.
- [ ] `tenant_id` nunca lido de header HTTP ou body — apenas do JWT assinado.
- [ ] `_reservar_estoque` e `_baixar_insumo` usam `estoque_repository.get_insumo_for_update` (SELECT FOR UPDATE).
- [ ] `aplicar_desconto` passa por `increment_version` CAS — retorna 409 com versão desatualizada.
- [ ] `cancelar_comanda` passa por `increment_version` CAS — retorna 409 com versão desatualizada.
- [ ] Teste com duas threads simultâneas lançando o mesmo insumo: estoque final correto, sem lost update.
- [ ] Teste de `aplicar_desconto` com versão stale retorna 409.
- [ ] Teste de `cancelar_comanda` com versão stale retorna 409.

### Blocked by

Issue 1 — depende de `tenant_id` nas tabelas e RLS ativo para que a injeção de sessão seja significativa.

### User stories addressed

- User story 9: `tenant_id` lido do JWT, injetado na sessão do banco
- User story 31: reserva de estoque usa SELECT FOR UPDATE
- User story 32: `aplicar_desconto` passa pelo CAS de versão
- User story 33: `cancelar_comanda` passa pelo CAS de versão
- User story 34: nenhuma mutação de comanda ocorre sem CAS

---

## Issue 3 — Onboarding atômico de tenant

**Type:** HITL
**Blocked by:** Issue 1, Issue 2

### What to build

`TenantRepository` + `TenantService` responsáveis pelo fluxo atômico de criação de empresa: uma única transação que faz INSERT em `tenants`, clona os perfis padrão (Admin, Gerente, Caixa) a partir do seed `0035_seed_default_profiles.py`, cria o primeiro usuário admin, e cria a assinatura inicial em status `trial`. Se qualquer passo falhar, rollback total — sem tenant órfão nem usuário sem perfil.

Endpoints restritos ao superadmin Flow4Tech: `POST /admin/tenants`, `GET /admin/tenants/{id}`, `PATCH /admin/tenants/{id}`.

**Ponto HITL:** decidir mecanismo de autenticação do superadmin Flow4Tech (claim especial `is_superadmin` no JWT, token fixo via env var, ou role separada). Decisão afeta todas as rotas `/admin/`.

### Acceptance criteria

- [ ] `POST /admin/tenants` cria tenant + perfis clonados + usuário admin + assinatura trial em transação única.
- [ ] Falha simulada em qualquer passo (ex: email duplicado) resulta em rollback completo — nenhum registro órfão no banco.
- [ ] Tenant criado tem `admin_user_id` preenchido.
- [ ] Email do usuário admin é obrigatório no onboarding.
- [ ] Perfis clonados (Admin, Gerente, Caixa) têm `tenant_id` do novo tenant — alterações nesses perfis não afetam outros tenants.
- [ ] `GET /admin/tenants/{id}` retorna dados do tenant incluindo status da assinatura.
- [ ] `PATCH /admin/tenants/{id}` permite atualizar `nome_fantasia` e `status`.
- [ ] Rotas `/admin/` retornam 403 para usuários não-superadmin.
- [ ] Teste de transação atômica: mock de falha no passo de criação de usuário → banco não tem registro de tenant nem perfis.

### Blocked by

- Bloqueado por Issue 1 (tabela `tenants` e RLS)
- Bloqueado por Issue 2 (get_db com injeção de tenant_id)

### User stories addressed

- User story 1: admin Flow4Tech cria tenant via painel interno
- User story 2: perfis padrão clonados automaticamente ao criar tenant
- User story 3: transação atômica — sem tenants órfãos em caso de falha
- User story 4: `admin_user_id` registrado no tenant
- User story 5: email do admin obrigatório no onboarding
- User story 8: funcionário sem email faz login com username + senha

---

## Issue 4 — JWT multi-tenant ✅

**Type:** AFK
**Blocked by:** Issue 1, Issue 3

### What to build

Adicionar claims `tenant_id` (int) e `subscription_status` (str) ao access token. No refresh do token, reler `assinaturas.status` do banco e reemitir access token com valor atual — propagação de suspensão para todos os funcionários no próximo refresh sem invalidar sessões individuais. TTL do access token ≤ 15 minutos.

Remover todos os `TENANT_ID = 1` hardcoded restantes em `auth_service`, `users_service`, `profiles_service`.

### Acceptance criteria

- [ ] Access token contém claims `tenant_id`, `permissions` e `subscription_status`.
- [ ] Refresh token endpoint relê `assinaturas.status` do banco antes de emitir novo access token.
- [ ] Novo access token emitido no refresh tem `subscription_status` atual (não cacheado do login original).
- [ ] TTL do access token configurado em ≤ 15 minutos.
- [ ] Nenhum `TENANT_ID = 1` hardcoded remanescente nos serviços de auth, users e profiles.
- [ ] Teste: login retorna JWT com `tenant_id` correto do usuário.
- [ ] Teste: suspender assinatura via UPDATE direto no banco → próximo refresh retorna token com `subscription_status = suspensa`.

### Blocked by

- Bloqueado por Issue 1 (tenant_id existe nas tabelas)
- Bloqueado por Issue 3 (tenant existe para ser referenciado no JWT)

### User stories addressed

- User story 9: JWT contém `tenant_id`, `permissions` e `subscription_status`
- User story 19: refresh relê `subscription_status` do banco — suspensão propaga no próximo refresh

---

## Issue 5 — Sistema de assinaturas e billing manual ✅

**Type:** AFK
**Blocked by:** Issue 3, Issue 4

### What to build

Tabelas `planos`, `assinaturas` e `pagamentos_assinatura`. Máquina de estados: `trial → ativa → vencida / cancelada / suspensa`. Dependency `require_active_subscription` retorna 402 se `subscription_status ∉ {ativo, trial}`. Job diário no scheduler existente marca como `vencida` toda assinatura com `data_vencimento < CURRENT_DATE`. Billing manual: admin registra pagamento diretamente, sem gateway.

Endpoints admin: `POST /admin/tenants/{id}/payments`, `PATCH /admin/tenants/{id}/subscription`, `GET /admin/plans`, `POST /admin/plans`.

### Acceptance criteria

- [ ] Migration cria `planos`, `assinaturas`, `pagamentos_assinatura` com campos do PRD.
- [ ] Tenant recém-criado (via Issue 3) já nasce com assinatura em status `trial`.
- [ ] `require_active_subscription` retorna 402 para `subscription_status = vencida` ou `suspensa`.
- [ ] `require_active_subscription` passa (não bloqueia) para `ativa` e `trial`.
- [ ] Rota de negócio qualquer com token `vencida` retorna 402.
- [ ] Job diário: assinatura com `data_vencimento = yesterday` muda de `ativa` → `vencida` após rodar.
- [ ] `PATCH /admin/tenants/{id}/subscription` com `status=suspensa` bloqueia acesso imediatamente (sem tocar registros de usuário).
- [ ] `PATCH /admin/tenants/{id}/subscription` com `status=ativa` + nova `data_vencimento` restaura acesso.
- [ ] `POST /admin/tenants/{id}/payments` registra pagamento com `gateway_ref` opcional.
- [ ] Teste: token com `subscription_status=vencida` → 402 em rota de comanda.
- [ ] Teste: job com assinatura vencida ontem → status atualizado para `vencida`.

### Blocked by

- Bloqueado por Issue 3 (tenant existe para ter assinatura)
- Bloqueado por Issue 4 (JWT carrega `subscription_status` para o middleware verificar)

### User stories addressed

- User story 11: suspensão com 1 UPDATE em `assinaturas`
- User story 12: reativação com 1 UPDATE + nova `data_vencimento`
- User story 13: job diário marca vencida automaticamente
- User story 14: pagamento manual registrado em `pagamentos_assinatura`
- User story 15: planos criados e editados via admin
- User story 16: novo tenant começa em trial
- User story 20: admin pode suspender tenant imediatamente

---

## Issue 6 — Frontend: SubscriptionGuard ✅

**Type:** HITL
**Blocked by:** Issue 4, Issue 5

### What to build

Interceptor HTTP que captura respostas 402 e decide o fluxo por perfil lido do JWT. Admin → redireciona para tela dedicada "Assinatura Vencida" com instruções de regularização e contato Flow4Tech. Demais perfis (Garçom, Caixa, Gerente) → exibe modal/tela "Conta suspensa — procure o responsável" sem expor informações de billing.

**Ponto HITL:** definir layout, copy e ação primária das duas telas (a tela de Admin pode precisar de aprovação de design antes de implementar).

### Acceptance criteria

- [ ] Interceptor HTTP captura 402 globalmente (não por rota).
- [ ] Perfil Admin → roteado para tela `/assinatura-vencida` com instrução de pagamento e contato Flow4Tech.
- [ ] Perfis não-admin → exibe modal ou tela bloqueante "Conta suspensa — procure o responsável".
- [ ] Tela de Admin não é acessível a perfis não-admin (guard de rota).
- [ ] Após regularização (novo token com `subscription_status=ativa`), usuário retorna ao fluxo normal sem reload manual.
- [ ] Sem regressão no fluxo de login e rotas normais (interceptor não afeta respostas não-402).

### Blocked by

- Bloqueado por Issue 4 (JWT com `subscription_status` disponível no cliente)
- Bloqueado por Issue 5 (backend retorna 402 efetivamente)

### User stories addressed

- User story 17: Admin vê tela com instruções de regularização
- User story 18: funcionário vê mensagem simples sem dados de billing
- User story 19: após novo refresh (status atualizado), acesso restaurado sem logout

---

## Issue 7 — Auditoria de caixa (backend)

**Type:** AFK
**Blocked by:** Issue 1

### What to build

Tabelas `caixa_sessoes` e `caixa_movimentos`, ambas com `tenant_id` + RLS. Índice único parcial garante no máximo uma sessão aberta por tenant: `CREATE UNIQUE INDEX ... WHERE status = 'aberta'`.

`CaixaService` + `CaixaRepository` com operações: `abrir_caixa` (registra fundo de troco), `fechar_caixa` (calcula diferença: `valor_abertura + pagamentos_em_dinheiro + suprimentos - sangrias`), `registrar_sangria`, `registrar_suprimento`, `get_sessao_aberta`.

Nova permissão `caixa` adicionada ao universo de telas — `require_permission("caixa")` protege todos os endpoints.

### Acceptance criteria

- [ ] Migration cria `caixa_sessoes` e `caixa_movimentos` com campos do PRD + `tenant_id` + RLS.
- [ ] Índice único parcial impede segunda sessão aberta no mesmo tenant.
- [ ] `POST /caixa/abrir` abre sessão com `valor_abertura`; retorna erro se já há sessão aberta.
- [ ] `POST /caixa/fechar` fecha sessão, registra `valor_informado` e calcula `diferenca = valor_esperado - valor_informado`.
- [ ] `valor_esperado = valor_abertura + SUM(pagamentos dinheiro na janela) + SUM(suprimentos) - SUM(sangrias)`.
- [ ] `POST /caixa/movimentos` registra sangria ou suprimento com `valor` e `motivo`.
- [ ] `GET /caixa/sessao` retorna sessão aberta do tenant atual ou 404.
- [ ] Tentativa de abrir segunda sessão retorna 409.
- [ ] Rotas de caixa retornam 403 sem permissão `caixa` no JWT.
- [ ] Sessões de outros tenants não visíveis (RLS).
- [ ] Teste de fechamento: `diferenca` calculada bate com `valor_abertura + movimentos - sangrias`.
- [ ] Teste de dupla abertura: segundo `POST /caixa/abrir` retorna 409.

### Blocked by

- Bloqueado por Issue 1 (tenant_id + RLS nas tabelas)

### User stories addressed

- User story 21: operador abre caixa com fundo de troco
- User story 22: sistema impede segunda sessão aberta
- User story 23: sangria registrada com valor e motivo
- User story 24: suprimento registrado com valor e motivo
- User story 25: fechamento com valor contado informado pelo operador
- User story 26: valor calculado derivado de pagamentos + movimentos auditáveis
- User story 27: diferença exibida ao fechar
- User story 28: permissão `caixa` separada das permissões de comandas
- User story 29: observação opcional no fechamento
- User story 30: dados de caixa isolados por tenant via RLS

---

## Issue 8 — Rebranding Flow4Food

**Type:** AFK
**Blocked by:** None — pode começar imediatamente.

### What to build

Substituir todas as referências a "Matchpoint" por "Flow4Food" / "Flow4Tech" em frontend, backend e emails. Mudanças são puramente textuais — sem alteração de lógica.

Arquivos: `frontend/index.html`, `frontend/src/features/auth/LoginPage.tsx`, `frontend/src/components/layout/Topbar.tsx`, `frontend/src/features/auth/EsqueciSenhaPage.tsx`, `frontend/src/features/auth/RedefinirSenhaPage.tsx`, `frontend/src/pages/PlaceholderPage.tsx`, `backend/src/main.py`, `backend/src/services/auth_service.py`.

### Acceptance criteria

- [ ] `<title>` em `index.html` exibe "Flow4Food".
- [ ] Card de login exibe "Flow4Food" e "por Flow4Tech" visíveis.
- [ ] Topbar exibe marca "Flow4Food".
- [ ] Páginas de recuperação/redefinição de senha referenciam Flow4Food/Flow4Tech.
- [ ] `PlaceholderPage` sem referências a Matchpoint.
- [ ] `backend/src/main.py`: `title="Flow4Food API"` (visível no Swagger/OpenAPI).
- [ ] Email de reset de senha: assunto e corpo referenciam Flow4Food/Flow4Tech.
- [ ] Busca por "Matchpoint" no repositório retorna 0 resultados em arquivos de produto (exceto histórico git e docs de arquitetura).

### Blocked by

None — pode começar imediatamente.

### User stories addressed

- User story 35: "Flow4Food" no título do browser e interface
- User story 36: relação "Flow4Food — por Flow4Tech" no login e rodapé
- User story 37: título da API é "Flow4Food API"
- User story 38: emails de reset referenciam Flow4Food/Flow4Tech

---

## Issue 9 — Frontend: tela de caixa

**Type:** HITL
**Blocked by:** Issue 7

### What to build

Feature `/features/caixa/` com três fluxos principais:

1. **Abertura de sessão** — formulário para informar fundo de troco, botão abrir.
2. **Turno ativo** — registrar sangria (retirada) ou suprimento (aporte) com valor e motivo; exibir movimentos do turno.
3. **Fechamento** — formulário para valor contado na gaveta; exibir valor esperado, valor informado e diferença (quebra/sobra) antes de confirmar.

Guard de rota: só perfis com permissão `caixa` acessam.

**Ponto HITL:** layout das três telas (especialmente a tela de fechamento com a exibição da diferença).

### Acceptance criteria

- [ ] Rota protegida por permissão `caixa` — 403 ou redirect para perfis sem a permissão.
- [ ] Sem sessão aberta: exibe tela de abertura com campo de fundo de troco.
- [ ] Com sessão aberta: exibe tela de turno ativo com lista de movimentos e botões de sangria/suprimento/fechar.
- [ ] Formulário de sangria/suprimento: campos `tipo`, `valor` e `motivo`; confirma e atualiza lista.
- [ ] Tela de fechamento: campo `valor_contado`; exibe `valor_esperado` (calculado pelo backend), `valor_informado` e `diferença` antes de confirmar.
- [ ] Diferença positiva (sobra) e negativa (quebra) com cor distinta.
- [ ] Após fechar: redireciona para tela de abertura (próximo turno).
- [ ] Sem regressão em outras features ao adicionar a nova rota.

### Blocked by

- Bloqueado por Issue 7 (endpoints de caixa existem)

### User stories addressed

- User story 21: operador abre caixa informando fundo de troco
- User story 22: sistema impede abertura se sessão já existe (feedback claro na UI)
- User story 23: sangria registrada via formulário
- User story 24: suprimento registrado via formulário
- User story 25: fechamento com valor contado informado
- User story 27: diferença exibida com destaque visual
- User story 29: campo de observação no fechamento
