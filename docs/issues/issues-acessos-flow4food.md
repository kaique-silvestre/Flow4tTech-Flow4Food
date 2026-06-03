# Issues — Acessos Flow4Food

> Gerado a partir de `docs/prds/acessos-flow4food.md` — v1.0 (13/05/2026)
> Escopo: MVP apenas. Itens de roadmap (2FA, SSO, audit log) excluídos.

---

## Resumo

| Total | [BACKEND] | [FEAT] | [INT] | [REFACTOR] | [NAV] |
|-------|-----------|--------|-------|------------|-------|
| 8 | 3 | 2 | 1 | 1 | 1 |

| P0 | P1 | P2 |
|----|----|----|
| 3  | 4  | 1  |

---

## Análise de Reuso (o que já existe)

| Item | Status |
|------|--------|
| JWT access + refresh token | ✅ completo |
| Login / logout endpoints | ✅ completo |
| Rate limiting login (5/15min) | ✅ completo (implementado nesta sessão) |
| Password recovery (forgot/reset) | ✅ completo |
| Change own password | ✅ completo |
| CRUD users + profiles | ✅ completo |
| Frontend login / esqueci / redefinir senha | ✅ completo |
| Dynamic sidebar por permissão | ✅ completo |
| Tenants table + migration | ✅ completo (merge `main`) |
| Admin endpoint `POST /api/admin/tenants` | ✅ completo (merge `main`) |
| Tenant provisioning (perfis + admin user + assinatura trial) | ✅ completo (merge `main`) |
| `SUPERADMIN_TOKEN` config | ✅ completo |
| Assinaturas model | ✅ completo (migration 0045) |
| SMTP config (env vars) | ✅ parcial — vars existem, service de email ausente |
| `must_change_password` field | ❌ ausente |
| Email único por tenant (vs global) | ❌ ausente — atualmente global |
| CORS para `flow4tech.com.br` | ❌ ausente — apenas localhost + Vercel |
| Cookie cross-subdomain | ❌ ausente |
| Asaas webhook | ❌ ausente |
| Resend email service | ❌ ausente |
| 403 → logout automático no frontend | ❌ ausente (critério pendente de issues-permissoes) |
| Tela `criar-senha` (primeiro acesso) | ❌ ausente |

---

## Fase 1 — Bloqueadores (P0 — executar primeiro)

---

### #1 [BACKEND] Email único por tenant (não global)

**Priority:** P0
**Effort:** S
**Depends on:** —

#### Goal
Corrigir constraint de unicidade de email e username para ser por tenant, não global — permite que a mesma pessoa tenha conta em dois estabelecimentos diferentes.

#### Acceptance Criteria
- [ ] Migration: remover `UNIQUE(email)` global de `system_users`; adicionar `UNIQUE(tenant_id, email)`
- [ ] Migration: confirmar `UNIQUE(tenant_id, username)` (verificar se já existe assim ou é global)
- [ ] `POST /api/users` e `PUT /api/users/{id}` validam unicidade dentro do tenant, não globalmente
- [ ] `GET /api/users/check-email?email=X` valida dentro do tenant do usuário logado
- [ ] `GET /api/users/check-username?username=X` valida dentro do tenant do usuário logado
- [ ] `criar_tenant` em `tenant_service.py` verifica email do admin apenas globalmente (admin de tenant diferente pode ter mesmo email)
- [ ] Testes: criar user com email X no tenant 1 e email X no tenant 2 → ambos criam sem erro

#### Notes
Verificar `backend/src/services/users_service.py` — atualmente usa `get_user_by_email` sem filtro de tenant. Ajustar para passar `tenant_id`. Migration é additive: remove uma constraint, adiciona outra.

---

### #2 [BACKEND] Campo `must_change_password` + fluxo de primeiro acesso

**Priority:** P0
**Effort:** M
**Depends on:** —

#### Goal
Permitir que Admin crie usuários sem senha (ou com senha provisória) e force troca no primeiro login, habilitando o fluxo de onboarding do PRD.

#### Acceptance Criteria
- [ ] Migration: adicionar coluna `must_change_password BOOLEAN NOT NULL DEFAULT false` em `system_users`
- [ ] `POST /api/auth/login` — se `must_change_password=true`, retornar HTTP 200 com campo `must_change_password: true` no body (não bloquear — deixar frontend redirecionar)
- [ ] `POST /api/auth/change-password` — ao completar a troca, setar `must_change_password=false`
- [ ] `criar_tenant` em `tenant_service.py` — ao criar admin do tenant, setar `must_change_password=true` e `password_hash` de senha provisória gerada (8 chars alfanumérico)
- [ ] Resposta de `criar_tenant` retorna `admin_temp_password` (somente no momento da criação)
- [ ] Frontend: ao detectar `must_change_password: true` no login, redirecionar para `/criar-senha`
- [ ] Frontend: tela `/criar-senha` — campos "Nova senha" + "Confirmar nova senha"; chama `POST /api/auth/change-password`; redireciona para `/dashboard` ao concluir

#### Notes
Não usar token de reset para primeiro acesso — o usuário já está autenticado via JWT. A tela `/criar-senha` é uma rota protegida (exige JWT válido). Senha provisória deve ter no mínimo 8 chars para passar na validação.

---

### #3 [BACKEND] CORS para domínios de produção

**Priority:** P0
**Effort:** XS
**Depends on:** —

#### Goal
Permitir que o site `flow4tech.com.br` e o sistema `app.flow4tech.com.br` se comuniquem corretamente em produção.

#### Acceptance Criteria
- [ ] `CORS_ORIGINS` default em `config.py` inclui `https://flow4tech.com.br` e `https://app.flow4tech.com.br`
- [ ] `.env.example` atualizado com os domínios de produção documentados
- [ ] `allow_credentials=True` já configurado (verificar — já existe no main.py)
- [ ] Preflight request (`OPTIONS`) de `https://flow4tech.com.br` retorna 200 com headers corretos

#### Notes
Alteração mínima em `src/core/config.py` linha 20. Não sobrescrever — concatenar aos existentes. Em produção, `CORS_ORIGINS` deve ser definido via env var no Railway/Render.

---

## Fase 2 — Core MVP (P1 — executar após Fase 1)

---

### #4 [BACKEND] Cookie cross-subdomain para produção

**Priority:** P1
**Effort:** XS
**Depends on:** #3

#### Goal
Garantir que o cookie de refresh token funcione corretamente entre `flow4tech.com.br` e `app.flow4tech.com.br` em produção.

#### Acceptance Criteria
- [ ] `_set_refresh_cookie` em `auth.py` usa `domain=".flow4tech.com.br"` quando `ENV=prod`
- [ ] Em `ENV=dev`, `domain` não é setado (browsers locais não aceitam wildcard domain)
- [ ] `samesite="none"` já configurado (verificar — já existe)
- [ ] Cookie de refresh token funciona ao navegar entre site e sistema no mesmo subdomínio

#### Notes
Em `auth.py`, o cookie já tem `samesite="none"` e `secure=True`. Só falta o `domain` condicional. Usar `get_settings().ENV` para decidir.

---

### #5 [INT] Webhook Asaas → provisionamento automático de tenant

**Priority:** P1
**Effort:** L
**Depends on:** #1, #2

#### Goal
Automatizar criação de tenant quando cliente paga assinatura via Asaas, eliminando necessidade de criação manual pelo superadmin.

#### Acceptance Criteria
- [ ] `POST /api/admin/webhook/asaas` — endpoint público (sem auth, mas com verificação de assinatura Asaas)
- [ ] Verificar header `asaas-access-token` contra `ASAAS_WEBHOOK_TOKEN` env var
- [ ] Evento `PAYMENT_CONFIRMED` → chamar `criar_tenant` com dados do cliente
- [ ] Evento `SUBSCRIPTION_CANCELLED` → setar `tenant.status = "inativo"`
- [ ] Idempotente: se tenant com `cnpj` já existe, não duplicar — apenas atualizar assinatura
- [ ] Em caso de erro no provisionamento, retornar 500 (Asaas vai retentar)
- [ ] Log estruturado de cada evento recebido
- [ ] `ASAAS_WEBHOOK_TOKEN` adicionado ao `config.py` e `.env.example`

#### Notes
Dados disponíveis no payload Asaas: `customer.name`, `customer.email`, `customer.cpfCnpj`. Username do admin = parte do email antes do `@`. Senha provisória gerada pelo sistema (fluxo do #2). Não depende de Resend estar pronto — logar URL de primeiro acesso se email não configurado.

---

### #6 [INT] Serviço de email (Resend) — boas-vindas e primeiro acesso

**Priority:** P1
**Effort:** M
**Depends on:** #2

#### Goal
Enviar email de boas-vindas com link de primeiro acesso quando novo tenant é criado, seja via webhook ou via admin manual.

#### Acceptance Criteria
- [ ] Instalar `resend` Python SDK (`pip install resend`) + adicionar ao `pyproject.toml`
- [ ] `RESEND_API_KEY` adicionado ao `config.py` e `.env.example`
- [ ] `src/services/email_service.py` com método `send_first_access(user_email, user_name, temp_password)`
- [ ] Email enviado após `criar_tenant` bem-sucedido (tanto via admin quanto via webhook)
- [ ] Se `RESEND_API_KEY` vazio: logar credenciais no terminal (fallback dev)
- [ ] Template de email: assunto "Bem-vindo ao Flow4Food — seu acesso", body com login + senha provisória + link para sistema

#### Notes
PRD menciona Resend já configurado no site Next.js. Reutilizar a mesma API key. Não usar SMTP para este fluxo — Resend é mais confiável. SMTP pode ficar para recuperação de senha (já implementado).

---

### #7 [FEAT] Frontend — tela `/criar-senha` (primeiro acesso)

**Priority:** P1
**Effort:** S
**Depends on:** #2

#### Goal
Dar ao usuário recém-criado uma tela dedicada para definir sua própria senha antes de acessar o sistema.

#### Acceptance Criteria
- [ ] Rota `/criar-senha` criada em `App.tsx` — protegida por `RequireAuth`
- [ ] Componente `CriarSenhaPage.tsx` em `src/features/auth/`
- [ ] Campos: "Nova senha" + "Confirmar nova senha" (mínimo 6 chars, validação Zod)
- [ ] Chama `POST /api/auth/change-password` com `current_password = senha_provisória` — **não**: reutilizar o endpoint existente sem current_password
- [ ] Alternativa: criar endpoint `POST /api/auth/set-first-password` que não exige `current_password` mas requer `must_change_password=true` no JWT
- [ ] Após sucesso: redirecionar para `/dashboard`
- [ ] `authStore` detecta `must_change_password: true` no login e redireciona automaticamente para `/criar-senha`

#### Notes
Visual idêntico à tela de redefinição de senha (`RedefinirSenhaPage.tsx`). Reutilizar layout. A diferença é que não há `current_password` — o usuário veio de senha provisória enviada por email.

---

## Fase 3 — Complementar MVP (P2)

---

### #8 [NAV] Site Flow4Tech — botão "Entrar" aponta para sistema

**Priority:** P2
**Effort:** XS
**Depends on:** —

#### Goal
Garantir que o botão "Entrar" no site público redirecione para o sistema, sem lógica de autenticação no site.

#### Acceptance Criteria
- [ ] No repo `flow4tech-site`, localizar componente com botão "Entrar" / "Meu acesso" (provavelmente no header/navbar)
- [ ] Alterar href para `https://app.flow4tech.com.br/login` (ou env var `NEXT_PUBLIC_APP_URL`)
- [ ] Nenhuma lógica de autenticação no site (zero `fetch`, zero JWT, zero cookies de auth)
- [ ] Em dev, apontar para `http://localhost:5173/login` via env var

#### Notes
Issue atua no repo `flow4tech-site` (repositório separado: `Flow4Tech-Site/flow4tech-website`). Verificar componente de header. Mudança é de 1-2 linhas mas requer acesso ao outro repo.

---

## Ordem de execução

```
Bloco 1 (paralelo, sem dependência entre si):
  #1  Email único por tenant
  #2  must_change_password + primeiro acesso (backend)
  #3  CORS domínios de produção

Bloco 2 (após Bloco 1):
  #4  Cookie cross-subdomain           (após #3)
  #5  Webhook Asaas                    (após #1 e #2)
  #6  Serviço de email Resend          (após #2)
  #7  Tela /criar-senha (frontend)     (após #2)

Bloco 3:
  #8  Site — botão Entrar              (independente, pode ser paralelo)
```
