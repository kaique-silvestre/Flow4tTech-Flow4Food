# Issues — Gerenciamento de Permissões por Perfil (MVP)

> Gerado a partir de `docs/permissoes-flow4food.md` — v1.0 (13/05/2026)
> Escopo: MVP apenas. Roadmap futuro (2FA, SSO, granularidade view/edit) excluído.

---

## Backend

---

### #1 [BE] Migrations: tabelas do sistema de permissões ✅

**Tipo:** task
**Labels:** backend, database, migrations

**Descrição:**
Criar migrations Alembic para as 4 tabelas do RBAC:

- `profiles` — id, tenant_id, name, description, is_system, created_at, updated_at
- `permissions` — id, profile_id, screen (enum dos 8 identificadores), can_access, created_at
- `users` — id, tenant_id, profile_id, name, username, email, password_hash, is_active, last_login, created_at, updated_at
- `password_resets` — id, user_id, token, expires_at, used_at, created_at

**Critérios de aceitação:**
- [x] `alembic upgrade head` roda sem erro em banco limpo
- [x] Constraints de unicidade: `username` único por tenant, `email` único globalmente
- [x] FK entre tabelas com `ON DELETE RESTRICT` onde aplicável
- [x] Enum/check constraint para coluna `screen` com os 8 identificadores válidos: `dashboard`, `comandas`, `compras`, `estoque`, `cadastros`, `relatorios`, `configuracoes`, `gestao_usuarios`

---

### #2 [BE] Seed: perfis padrão por tenant ✅

**Tipo:** task
**Labels:** backend, seed

**Descrição:**
Ao criar/ativar um tenant, inserir automaticamente os 3 perfis do sistema com suas permissões padrão:

| Perfil | is_system | Telas com acesso |
|--------|-----------|-----------------|
| Admin | true | todas (8/8) |
| Gerente | true | 6/8 (exceto `configuracoes` e `gestao_usuarios`) |
| Caixa | true | 3/8 (`dashboard`, `comandas`, `estoque`) |

**Critérios de aceitação:**
- [x] Perfil Admin criado com `is_system=true` e permissão em todas as telas
- [x] Perfis Admin, Gerente e Caixa não podem ser excluídos (constraint + validação no service)
- [x] Seed é idempotente (não duplica se rodar duas vezes)

---

### #3 [BE] Endpoint de autenticação (login + logout) ✅

**Tipo:** feature
**Labels:** backend, auth

**Descrição:**
`POST /api/auth/login` — autenticar usuário e retornar JWT.

Fluxo:
1. Campo `identifier` — se contém `@`, busca por email; senão, busca por username dentro do tenant
2. Verifica `is_active = true`
3. Valida senha via bcrypt
4. Gera JWT com payload: `user_id`, `tenant_id`, `username`, `profile_id`, `profile_name`, `permissions[]`
5. Atualiza `last_login`

`POST /api/auth/logout` — invalida token (blacklist ou estratégia stateless documentada).

**Critérios de aceitação:**
- [x] JWT expira em 8 horas
- [x] Resposta de erro nunca revela se é email ou senha incorretos — mensagem genérica
- [ ] Rate limiting: máximo 5 tentativas por IP em 15 minutos
- [x] Senha nunca aparece em logs ou response body
- [x] `password_hash` nunca retornado em nenhum endpoint

---

### #4 [BE] Middleware de autorização por tela ✅

**Tipo:** task
**Labels:** backend, auth, middleware

**Descrição:**
Middleware FastAPI que valida o JWT em todas as rotas protegidas e verifica se o usuário tem a permissão necessária para aquela rota.

**Critérios de aceitação:**
- [x] Request sem JWT válido → 401
- [x] JWT válido mas sem permissão para a rota → 403
- [x] Decorator/dependency injetável por rota: `require_permission("relatorios")`
- [x] Tenant isolado: usuário do tenant A não acessa dados do tenant B

---

### #5 [BE] CRUD de usuários ✅

**Tipo:** feature
**Labels:** backend, users

**Endpoints:**
- `GET /api/users` — listar (com busca por nome/username e filtro por perfil)
- `POST /api/users` — criar
- `PUT /api/users/{id}` — editar
- `DELETE /api/users/{id}` — excluir
- `PATCH /api/users/{id}/activate` — ativar/desativar

**Regras de negócio (validar no service, não só no frontend):**
- [x] Não pode excluir o último usuário Admin ativo → 409 com mensagem clara
- [x] Não pode desativar o último Admin ativo → 409
- [x] Não pode alterar o próprio perfil
- [x] Usuário não pode se excluir ou desativar
- [x] Username único por tenant — validar antes de salvar
- [x] Email único globalmente — validar antes de salvar
- [x] `GET /api/users/check-username?username=X` — endpoint de validação em tempo real
- [x] `GET /api/users/check-email?email=X` — endpoint de validação em tempo real
- [x] `POST /api/users/{id}/reset-password` — Admin redefine senha de outro usuário (gera nova senha provisória)

**Critérios de aceitação:**
- [x] Todos os endpoints exigem permissão `gestao_usuarios` (exceto check de unicidade)
- [x] `password_hash` nunca retornado
- [x] Validação de senha mínimo 6 caracteres no create

---

### #6 [BE] CRUD de perfis e permissões ✅

**Tipo:** feature
**Labels:** backend, profiles

**Endpoints:**
- `GET /api/profiles` — listar perfis do tenant com contagem de usuários
- `POST /api/profiles` — criar perfil customizado
- `PUT /api/profiles/{id}` — editar nome, descrição e permissões
- `DELETE /api/profiles/{id}` — excluir perfil customizado

**Regras de negócio:**
- [x] Perfis com `is_system=true` não podem ser excluídos → 409
- [x] Perfil Admin não pode ter permissões alteradas → 409
- [x] Não pode excluir perfil com usuários vinculados — retornar lista de usuários afetados para o frontend exibir
- [x] Ao salvar permissões, atualização é imediata para todos usuários com aquele perfil

**Critérios de aceitação:**
- [x] Todos os endpoints exigem permissão `gestao_usuarios`
- [x] `PUT /api/profiles/{id}` aceita array de `permissions` e recria registros

---

### #7 [BE] Recuperação de senha ✅

**Tipo:** feature
**Labels:** backend, auth, email

**Endpoints:**
- `POST /api/auth/forgot-password` — solicitar reset
- `GET /api/auth/reset-password/{token}` — validar token e obter nome do usuário
- `POST /api/auth/reset-password` — definir nova senha com token

**Fluxo:**
1. Busca usuário por email
2. Se encontrou: invalida tokens anteriores, gera UUID, salva em `password_resets` com `expires_at = now + 1h`
3. Envia email via SMTP (env vars `SMTP_HOST/PORT/USER/PASS/FROM`). Se SMTP não configurado, loga URL no terminal
4. Se não encontrou: retorna a **mesma mensagem de sucesso** (não revelar se email existe)
5. Ao redefinir: valida token (existe, não expirado, não usado), atualiza `password_hash`, marca `used_at`

**Critérios de aceitação:**
- [x] Token tem validade de 1 hora e uso único
- [x] Resposta sempre genérica independente de o email existir
- [x] JWT stateless — sessões anteriores expiram naturalmente em 8h
- [x] Email via SMTP configurável por env vars; fallback: log da URL no terminal

---

### #8 [BE] Alterar própria senha ✅

**Tipo:** feature
**Labels:** backend, auth

**Endpoint:** `POST /api/auth/change-password`

**Critérios de aceitação:**
- [x] Requer JWT válido (qualquer perfil)
- [x] Valida senha atual antes de aceitar nova
- [x] Nova senha mínimo 6 caracteres
- [x] Não retorna nem loga senha em nenhum momento

---

## Frontend

---

### #9 [FE] Tela de login ✅

**Tipo:** feature
**Labels:** frontend, auth

**Descrição:**
Tela pública `/login` conforme wireframe da seção 7.1.

**Critérios de aceitação:**
- [x] Campo único `Email ou usuário` + campo `Senha`
- [ ] Botão `ENTRAR` + link `Esqueci minha senha`
- [x] Toast vermelho em falha: "Email/usuário ou senha inválidos" (mensagem genérica)
- [x] Redireciona para `/dashboard` após login bem-sucedido
- [x] JWT armazenado em `localStorage` (chave `matchpoint_jwt`)

---

### #10 [FE] Contexto de autenticação e guards de rota ✅

**Tipo:** task
**Labels:** frontend, auth

**Descrição:**
Contexto global com estado do usuário logado e sistema de proteção de rotas baseado em permissões do JWT.

**Critérios de aceitação:**
- [x] `authStore` (Zustand) expõe: `user`, `token`, `setToken`, `clearToken` — `user` contém `permissions[]`
- [x] Hook `usePermission("screen")` e `usePermissions()` — verifica acesso
- [x] `RequireAuth` component — redireciona para `/login` se sem token
- [x] 401 recebido → redireciona para `/login`
- [ ] 403 recebido do backend → logout automático + toast: "Suas permissões foram alteradas. Por favor, faça login novamente."

---

### #11 [FE] Menu lateral dinâmico ✅

**Tipo:** task
**Labels:** frontend, auth

**Descrição:**
Menu lateral renderiza apenas as opções que o usuário tem permissão, baseado no `permissions[]` do JWT.

**Critérios de aceitação:**
- [x] Itens sem permissão não aparecem (não apenas desabilitados — removidos do DOM)
- [x] Logout disponível no menu do usuário para qualquer perfil
- [x] Toast verde ao fazer logout: "Sessão encerrada"

---

### #12 [FE] Tela gestão de usuários ✅

**Tipo:** feature
**Labels:** frontend, users

**Rota:** `/configuracoes/usuarios`
**Acesso:** apenas perfil com permissão `gestao_usuarios`

**Descrição:** Conforme wireframe da seção 6.1.

**Critérios de aceitação:**
- [x] Tabela com: Nome, Usuário, Email, Perfil, Status (Ativo/Inativo)
- [x] Busca em tempo real por nome ou username
- [x] Filtro por perfil (dropdown)
- [x] Ações por linha: Editar, Resetar senha, Ativar/Desativar, Excluir
- [x] Usuário não vê botão de excluir/desativar para si mesmo
- [x] Botão de excluir último Admin desabilitado com tooltip explicativo
- [x] Aba "Perfis" integrada na mesma página
- [x] Estado vazio tratado

---

### #13 [FE] Modal cadastro/edição de usuário ✅

**Tipo:** feature
**Labels:** frontend, users

**Descrição:** Conforme wireframe da seção 6.2.

**Critérios de aceitação:**
- [x] Campos: Nome completo, Usuário (login), Email, Perfil (select), Senha provisória, Ativo (checkbox)
- [x] Validação em tempo real de username único (debounce 400ms → `GET /api/users/check-username`)
- [x] Validação em tempo real de email único (debounce 400ms → `GET /api/users/check-email`)
- [x] Validação de formato de email
- [x] Senha mínimo 6 caracteres com feedback inline
- [x] No modo edição: campo senha some, substituído por botão "Redefinir senha"
- [x] Perfil obrigatório (select sem valor vazio aceitável)
- [x] Botões: `CANCELAR` e `SALVAR USUÁRIO`

---

### #14 [FE] Tela gestão de perfis ✅

**Tipo:** feature
**Labels:** frontend, profiles

**Rota:** `/configuracoes/usuarios` (aba "Perfis" dentro da página)
**Acesso:** apenas perfil com permissão `gestao_usuarios`

**Descrição:** Conforme wireframe da seção 6.3.

**Critérios de aceitação:**
- [x] Tabela com: Nome, Usuários vinculados, Permissões (X/8), Sistema (✓), Ações
- [x] Perfis `is_system=true` exibem ícone ✓ e não têm botão excluir
- [x] Perfil Admin tem botão `Ver` (somente leitura) ao invés de `Editar`
- [x] Excluir perfil com usuários vinculados → modal de confirmação listando usuários afetados
- [x] Botão `+ NOVO PERFIL`

---

### #15 [FE] Modal cadastro/edição de perfil ✅

**Tipo:** feature
**Labels:** frontend, profiles

**Descrição:** Conforme wireframe da seção 6.4.

**Critérios de aceitação:**
- [x] Campos: Nome do perfil, Descrição (opcional)
- [x] Lista de 8 checkboxes de permissão com nome amigável e identificador
- [x] Para perfil Admin: todos checkboxes marcados e desabilitados (somente leitura)
- [x] Exibe contagem de usuários com o perfil: "Usuários com este perfil: N (Nome)"
- [x] Toast informativo ao salvar: "Permissões atualizadas para N usuários"
- [x] Botões: `CANCELAR` e `SALVAR PERFIL`

---

### #16 [FE] Modal alterar própria senha ✅

**Tipo:** feature
**Labels:** frontend, auth

**Acesso:** qualquer usuário logado — menu do usuário → "Alterar senha"

**Descrição:** Conforme wireframe da seção 6.5.

**Critérios de aceitação:**
- [x] Campos: Senha atual, Nova senha, Confirmar nova senha
- [x] Validação inline: nova senha mínimo 6 caracteres
- [x] Validação inline: senhas não coincidem
- [x] Botões: `CANCELAR` e `ALTERAR`
- [x] Toast verde em sucesso: "Senha alterada com sucesso"

---

### #17 [FE] Fluxo de recuperação de senha ✅

**Tipo:** feature
**Labels:** frontend, auth

**Rotas:** `/esqueci-senha` e `/redefinir-senha?token=TOKEN`

**Descrição:** Conforme wireframes das seções 8.2 e 8.4.

**Critérios de aceitação:**
- [x] Tela `/esqueci-senha`: campo email + botão `ENVIAR LINK` + link `← Voltar ao login`
- [x] Sempre exibe mensagem de sucesso genérica independente de o email existir
- [x] Tela `/redefinir-senha`: exibe nome do usuário (obtido via token), campos nova senha + confirmação
- [x] Token inválido/expirado → mensagem "Link expirado. Solicite um novo." + link para `/esqueci-senha`
- [x] Token já usado → mensagem "Link já utilizado. Solicite um novo se precisar."
- [x] Sucesso → toast verde "Senha redefinida com sucesso" + redirect para `/login`

---

## Ordem sugerida de implementação

```
Sprint 1 — Fundação
  #1  Migrations
  #2  Seed perfis padrão
  #3  Auth login/logout
  #4  Middleware autorização
  #9  FE tela login
  #10 FE auth context + guards
  #11 FE menu dinâmico

Sprint 2 — Gestão de usuários e perfis
  #5  BE CRUD usuários
  #6  BE CRUD perfis
  #12 FE tela gestão usuários
  #13 FE modal usuário
  #14 FE tela gestão perfis
  #15 FE modal perfil

Sprint 3 — Senhas
  #7  BE recuperação de senha
  #8  BE alterar própria senha
  #16 FE modal alterar senha
  #17 FE fluxo recuperação senha
```

---

## Fora do escopo (MVP)

- Tabela `access_logs` / auditoria (opcional no MVP conforme doc)
- Granularidade view/edit/delete por tela
- Permissões por funcionalidade (ex: "pode aplicar desconto")
- 2FA, SSO, política de senha forte
- Permissões por horário ou valor
