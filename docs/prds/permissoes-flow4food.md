# Gerenciamento de Permissões por Perfil — Sistema Flow4Food

> Documentação técnica e funcional do sistema de controle de acesso por perfil.
> Versão: 1.0 — 13/05/2026
> Status: Em planejamento — feature a ser implementada

---

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Conceitos Fundamentais](#2-conceitos-fundamentais)
3. [Modelagem de Dados](#3-modelagem-de-dados)
4. [Perfis Pré-Cadastrados](#4-perfis-pré-cadastrados)
5. [Regras de Negócio](#5-regras-de-negócio)
6. [Telas do Sistema](#6-telas-do-sistema)
7. [Fluxo de Autenticação](#7-fluxo-de-autenticação)
8. [Recuperação de Senha](#8-recuperação-de-senha)
9. [Controle de Acesso em Tempo de Execução](#9-controle-de-acesso-em-tempo-de-execução)
10. [Auditoria e Segurança](#10-auditoria-e-segurança)
11. [Casos de Borda e Validações](#11-casos-de-borda-e-validações)
12. [Roadmap Futuro](#12-roadmap-futuro)

---

## 1. Visão Geral

O sistema Flow4Food implementa um modelo de **RBAC simplificado (Role-Based Access Control)**: cada usuário tem um perfil atribuído, e o perfil define quais telas do sistema o usuário pode acessar.

### Por Que Esse Modelo

- **Simples de entender:** o Admin pensa "quais telas o caixa pode acessar?" e marca checkboxes
- **Escalável:** novos perfis podem ser criados a qualquer momento
- **Auditável:** cada ação é vinculada a um usuário identificado
- **Padrão de mercado:** modelo usado por praticamente todos os sistemas de gestão

### Princípio Norteador

> **Cada pessoa que opera o sistema tem seu próprio usuário.** Mesmo que duas pessoas façam a mesma função, cada uma tem login próprio. Isso garante auditoria, responsabilidade e troca de funcionários sem trauma.

---

## 2. Conceitos Fundamentais

### Entidades Principais

**Usuário (`user`)**
Pessoa física que opera o sistema. Tem login, senha, email e está vinculado a um perfil.

**Perfil (`profile`)**
Conjunto nomeado de permissões. Exemplo: "Admin", "Caixa", "Gerente". Cada perfil é vinculado a um conjunto de permissões.

**Permissão (`permission`)**
Define se um perfil pode ou não acessar determinada tela do sistema. No MVP, é binária (acesso sim / acesso não).

**Tenant (`tenant`)**
Cada restaurante/bar é um tenant. Usuários, perfis e permissões são isolados por tenant. Um usuário do "Restaurante A" jamais vê dados do "Restaurante B".

### Relacionamentos

```
TENANT (1) ──── (N) USUÁRIOS
   │
   └─── (N) PERFIS
              │
              └─── (N) PERMISSÕES (por tela)
```

Cada **usuário** pertence a **um tenant** e tem **um perfil**.
Cada **perfil** pertence a **um tenant** e tem **várias permissões**.

---

## 3. Modelagem de Dados

### Tabela: `profiles` (perfis)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único |
| `tenant_id` | UUID | Referência ao tenant |
| `name` | varchar(50) | Nome do perfil (ex: "Admin", "Caixa") |
| `description` | text | Descrição opcional do perfil |
| `is_system` | boolean | Se é perfil do sistema (não pode ser excluído) |
| `created_at` | timestamp | Data de criação |
| `updated_at` | timestamp | Última atualização |

### Tabela: `permissions` (permissões do perfil)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único |
| `profile_id` | UUID | Referência ao perfil |
| `screen` | varchar(50) | Identificador da tela (ex: "dashboard", "comandas") |
| `can_access` | boolean | Pode acessar a tela? |
| `created_at` | timestamp | Data de criação |

> **Decisão MVP:** apenas `can_access` (acesso sim/não). Granularidade view/edit fica para evolução futura.

### Tabela: `users` (usuários)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único |
| `tenant_id` | UUID | Referência ao tenant |
| `profile_id` | UUID | Referência ao perfil |
| `name` | varchar(100) | Nome completo |
| `username` | varchar(50) | Login curto (único por tenant) |
| `email` | varchar(150) | Email (único globalmente, usado para recuperação de senha) |
| `password_hash` | varchar(255) | Hash bcrypt da senha (NUNCA texto puro) |
| `is_active` | boolean | Usuário ativo? Se false, não consegue logar |
| `last_login` | timestamp | Último login bem-sucedido |
| `created_at` | timestamp | Data de criação |
| `updated_at` | timestamp | Última atualização |

### Tabela: `password_resets` (recuperação de senha)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único |
| `user_id` | UUID | Referência ao usuário |
| `token` | varchar(255) | Token único de recuperação |
| `expires_at` | timestamp | Validade do token (1 hora após criação) |
| `used_at` | timestamp | Quando o token foi usado (null se ainda válido) |
| `created_at` | timestamp | Data de criação |

### Tabela: `access_logs` (auditoria — opcional no MVP)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único |
| `user_id` | UUID | Usuário que acessou |
| `action` | varchar(100) | Ação realizada (login, logout, denied) |
| `screen` | varchar(50) | Tela acessada ou tentada |
| `ip_address` | varchar(45) | IP de origem |
| `user_agent` | text | Navegador/dispositivo |
| `created_at` | timestamp | Quando ocorreu |

---

## 4. Perfis Pré-Cadastrados

Ao criar um novo tenant (assinatura ativada), o sistema cria automaticamente os seguintes perfis padrão:

### Admin
- **is_system:** true (não pode ser excluído)
- **Acesso:** todas as telas do sistema
- **Quem usa:** dono do estabelecimento, sócios

### Caixa
- **is_system:** true
- **Acesso padrão:** Dashboard, Comandas, Estoque (somente visualização)
- **Quem usa:** operador de caixa
- **Pode ser editado:** sim, o Admin pode ajustar permissões

### Gerente
- **is_system:** true
- **Acesso padrão:** todas as telas exceto Configurações e Gestão de Usuários
- **Quem usa:** gerente do estabelecimento
- **Pode ser editado:** sim

> **Observação:** o Admin pode criar perfis customizados a qualquer momento (ex: "Caixa Noturno", "Sócio Investidor").

### Telas do Sistema Disponíveis para Permissão

Lista de identificadores de tela que aparecem nos checkboxes de configuração de perfil:

| Identificador | Nome amigável |
|---------------|---------------|
| `dashboard` | Dashboard |
| `comandas` | Comandas |
| `compras` | Compras |
| `estoque` | Estoque |
| `cadastros` | Cadastros |
| `relatorios` | Relatórios |
| `configuracoes` | Configurações |
| `gestao_usuarios` | Gestão de Usuários e Perfis |

---

## 5. Regras de Negócio

### 5.1 Proteção do Perfil Admin

- O perfil **Admin** tem `is_system: true` e **não pode ser excluído**
- O perfil **Admin** tem acesso a **todas as telas** e isso **não pode ser alterado**
- A tela de edição de perfil **bloqueia visualmente** os checkboxes quando o perfil é Admin

### 5.2 Garantia de Pelo Menos 1 Admin Ativo

- O sistema **NUNCA** pode ficar sem nenhum usuário com perfil Admin ativo
- Tentativa de:
  - Excluir o último Admin → **bloqueada** com mensagem clara
  - Desativar o último Admin → **bloqueada**
  - Trocar o perfil do último Admin → **bloqueada**

### 5.3 Auto-Edição

- Um usuário **não pode editar a si mesmo** na tela de gestão de usuários (exceto trocar a própria senha em uma tela separada)
- Um usuário **não pode excluir a si mesmo**
- Um usuário **não pode desativar a si mesmo**

### 5.4 Unicidade de Identificadores

| Campo | Escopo de unicidade |
|-------|---------------------|
| `username` | Único **por tenant** (Matheus pode ser "matheus" no Restaurante A e outro Matheus pode ser "matheus" no Restaurante B) |
| `email` | Único **globalmente** (necessário para recuperação de senha funcionar) |

### 5.5 Permissões de Gestão

Apenas usuários com acesso à tela `gestao_usuarios` podem:
- Criar novos usuários
- Editar usuários existentes
- Criar/editar/excluir perfis
- Resetar senhas de outros usuários

Por padrão, apenas o perfil **Admin** tem essa permissão. O Admin pode conceder a outros perfis se quiser.

### 5.6 Senhas

- Tamanho mínimo: **6 caracteres**
- Armazenamento: **hash bcrypt** com salt rounds = 10
- **NUNCA** armazenar senha em texto puro
- **NUNCA** retornar senha em respostas de API
- Reset de senha gera token único com validade de **1 hora**

---

## 6. Telas do Sistema

### 6.1 Tela: Gestão de Usuários

**Acesso:** apenas perfis com permissão `gestao_usuarios`
**Localização no menu:** Configurações → Usuários e Perfis

```
┌──────────────────────────────────────────────────────────────────┐
│  USUÁRIOS                                    [+ NOVO USUÁRIO]    │
│                                                                  │
│  🔍 [Buscar por nome ou usuário...]    Filtro: [Todos perfis ▼]  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Nome              Usuário    Email           Perfil  Status│  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ Matheus Gambini   matheus    matheus@...     Admin   Ativo │  │
│  │                                              [Editar][...]│  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ João Lopes        joao       joao@...        Caixa   Ativo │  │
│  │                                              [Editar][...]│  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ Ana Silva         ana        ana@...         Garçom  Inat. │  │
│  │                                              [Editar][...]│  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│                                          [Gerenciar perfis →]    │
└──────────────────────────────────────────────────────────────────┘
```

**Ações por linha:**
- Editar usuário
- Resetar senha
- Ativar/Desativar
- Excluir

### 6.2 Tela: Cadastro/Edição de Usuário

Modal ou tela dedicada, acionada por "+ NOVO USUÁRIO" ou "Editar".

```
┌──────────────────────────────────────────────────────────────────┐
│  CADASTRAR USUÁRIO                                          [✕]  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Nome completo:                                                  │
│  [____________________________________________]                  │
│                                                                  │
│  Usuário (login curto):                                          │
│  [____________________________________________]                  │
│  Será usado para login rápido. Ex: "joao", "matheus"             │
│                                                                  │
│  Email:                                                          │
│  [____________________________________________]                  │
│  Usado para recuperação de senha e notificações                  │
│                                                                  │
│  Perfil:                                                         │
│  [Selecione...                                            ▼]     │
│                                                                  │
│  Senha provisória:                                               │
│  [____________________________________________]                  │
│  Mínimo 6 caracteres. O usuário poderá alterar no primeiro login │
│                                                                  │
│  [ ] Usuário ativo                                               │
│                                                                  │
│                          [CANCELAR]      [SALVAR USUÁRIO]        │
└──────────────────────────────────────────────────────────────────┘
```

**Validações:**
- Username deve ser único no tenant (validação em tempo real)
- Email deve ser único globalmente (validação em tempo real)
- Email deve ter formato válido
- Senha mínimo 6 caracteres
- Perfil obrigatório

**Na edição:**
- Campo "Senha provisória" some — substituído por botão "Redefinir senha"
- Username pode ser alterado (com validação de unicidade)
- Email pode ser alterado (com validação de unicidade)

### 6.3 Tela: Gestão de Perfis

**Acesso:** apenas perfis com permissão `gestao_usuarios`
**Localização:** Configurações → Usuários e Perfis → Aba "Perfis"

```
┌──────────────────────────────────────────────────────────────────┐
│  PERFIS                                       [+ NOVO PERFIL]    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Nome      Usuários  Permissões             Sistema  Ações  │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ Admin     1         Acesso total (8/8)     ✓       [Ver]  │  │
│  │ Caixa     1         3 telas (3/8)          ✓       [Edit] │  │
│  │ Gerente   0         6 telas (6/8)          ✓       [Edit] │  │
│  │ Garçom    0         2 telas (2/8)                  [Edit] │  │
│  │                                                    [✕]    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Perfis com ✓ são perfis do sistema (não podem ser excluídos)    │
└──────────────────────────────────────────────────────────────────┘
```

**Observações:**
- Perfis com `is_system: true` não exibem botão de exclusão
- Perfis com usuários vinculados exibem confirmação antes de exclusão
- Perfil Admin tem botão "Ver" (somente leitura) ao invés de "Editar"

### 6.4 Tela: Cadastro/Edição de Perfil

```
┌──────────────────────────────────────────────────────────────────┐
│  EDITAR PERFIL: CAIXA                                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Nome do perfil:                                                 │
│  [Caixa                                                    ]     │
│                                                                  │
│  Descrição (opcional):                                           │
│  [Operador do caixa, responsável por fechamento de comandas]     │
│                                                                  │
│  PERMISSÕES DE ACESSO:                                           │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Tela                          Acesso                      │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │  📊 Dashboard                  [✓]                         │  │
│  │  🍺 Comandas                   [✓]                         │  │
│  │  🛒 Compras                    [ ]                         │  │
│  │  📦 Estoque                    [✓]                         │  │
│  │  📋 Cadastros                  [ ]                         │  │
│  │  📈 Relatórios                 [ ]                         │  │
│  │  ⚙️ Configurações              [ ]                         │  │
│  │  👥 Usuários e Perfis          [ ]                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Usuários com este perfil: 1 (João Lopes)                        │
│                                                                  │
│                          [CANCELAR]      [SALVAR PERFIL]         │
└──────────────────────────────────────────────────────────────────┘
```

**Observações:**
- Ao salvar, todos os usuários com este perfil terão suas permissões atualizadas imediatamente
- Se o usuário estiver logado quando a permissão for revogada, na próxima navegação ele será redirecionado da tela bloqueada
- Para perfil Admin, todos os checkboxes ficam marcados e desabilitados

### 6.5 Tela: Alterar Própria Senha

**Acesso:** qualquer usuário logado pode alterar a própria senha
**Localização:** menu de usuário (canto superior direito) → "Alterar senha"

```
┌────────────────────────────────────────┐
│  ALTERAR SENHA                     [✕] │
├────────────────────────────────────────┤
│                                        │
│  Senha atual:                          │
│  [____________________]                │
│                                        │
│  Nova senha:                           │
│  [____________________]                │
│  Mínimo 6 caracteres                   │
│                                        │
│  Confirmar nova senha:                 │
│  [____________________]                │
│                                        │
│            [CANCELAR]  [ALTERAR]       │
└────────────────────────────────────────┘
```

---

## 7. Fluxo de Autenticação

### 7.1 Tela de Login

```
┌────────────────────────────────────────┐
│                                        │
│           FLOW4FOOD                    │
│                                        │
│   ┌──────────────────────────────┐     │
│   │ Email ou usuário             │     │
│   └──────────────────────────────┘     │
│                                        │
│   ┌──────────────────────────────┐     │
│   │ Senha                        │     │
│   └──────────────────────────────┘     │
│                                        │
│   ┌──────────────────────────────┐     │
│   │           ENTRAR             │     │
│   └──────────────────────────────┘     │
│                                        │
│        Esqueci minha senha             │
│                                        │
└────────────────────────────────────────┘
```

### 7.2 Fluxo de Login

```
1. Usuário insere "email ou usuário" + senha
2. Sistema verifica:
   a. Se contém "@" → busca por email
   b. Senão → busca por username (dentro do tenant correto)
3. Se encontrou usuário:
   a. Verifica is_active = true
   b. Compara senha digitada com hash via bcrypt
4. Se autenticado:
   a. Carrega perfil do usuário
   b. Carrega permissões do perfil
   c. Gera token JWT com user_id, tenant_id, profile_id e permissões
   d. Atualiza last_login
   e. Redireciona para dashboard (ou primeira tela permitida)
5. Se falhou:
   a. Toast vermelho: "Email/usuário ou senha inválidos"
   b. NÃO especificar qual dos dois está errado (segurança)
```

### 7.3 Sessão

- Token JWT com expiração de **8 horas** (cobre um turno de trabalho)
- Renovação automática quando o usuário está ativo
- Logout explícito invalida o token

### 7.4 Logout

- Disponível no menu do usuário (canto superior direito)
- Limpa o token da sessão
- Redireciona para tela de login
- Toast verde: "Sessão encerrada"

---

## 8. Recuperação de Senha

### 8.1 Fluxo Completo

```
1. Usuário clica em "Esqueci minha senha"
    ↓
2. Tela pede o email cadastrado
    ↓
3. Usuário informa email
    ↓
4. Sistema:
   a. Busca usuário pelo email
   b. Se encontrou: gera token único, salva em password_resets, expira em 1h
   c. Envia email com link: flow4tech.com.br/redefinir-senha?token=ABC123
   d. Se NÃO encontrou: mostra a MESMA mensagem de sucesso (segurança — não revelar se email existe)
    ↓
5. Usuário recebe email
    ↓
6. Clica no link → tela de definição de nova senha
    ↓
7. Sistema valida token:
   a. Existe?
   b. Não expirou?
   c. Não foi usado?
    ↓
8. Se válido: usuário define nova senha
   a. Sistema atualiza password_hash
   b. Marca token como usado (used_at)
   c. Invalida todas as sessões ativas do usuário
   d. Toast verde: "Senha redefinida com sucesso"
   e. Redireciona para login
```

### 8.2 Tela: Esqueci Minha Senha

```
┌────────────────────────────────────────┐
│  RECUPERAR SENHA                       │
├────────────────────────────────────────┤
│                                        │
│  Informe seu email cadastrado.         │
│  Enviaremos um link para você criar    │
│  uma nova senha.                       │
│                                        │
│  ┌──────────────────────────────┐      │
│  │ seu@email.com                │      │
│  └──────────────────────────────┘      │
│                                        │
│  ┌──────────────────────────────┐      │
│  │      ENVIAR LINK             │      │
│  └──────────────────────────────┘      │
│                                        │
│       ← Voltar ao login                │
└────────────────────────────────────────┘
```

### 8.3 Email de Recuperação

**Assunto:** Recuperação de senha — Flow4Food

**Corpo:**
```
Olá [Nome do usuário],

Recebemos uma solicitação para redefinir sua senha no Flow4Food.

Clique no link abaixo para criar uma nova senha:
[BOTÃO: Redefinir minha senha]

Este link é válido por 1 hora.

Se você não solicitou esta alteração, ignore este email — sua senha permanecerá a mesma.

Equipe Flow4Tech
```

### 8.4 Tela: Definir Nova Senha

Acessada pelo link do email.

```
┌────────────────────────────────────────┐
│  DEFINIR NOVA SENHA                    │
├────────────────────────────────────────┤
│                                        │
│  Olá, Matheus!                         │
│  Crie sua nova senha abaixo.           │
│                                        │
│  Nova senha:                           │
│  ┌──────────────────────────────┐      │
│  │                              │      │
│  └──────────────────────────────┘      │
│  Mínimo 6 caracteres                   │
│                                        │
│  Confirmar nova senha:                 │
│  ┌──────────────────────────────┐      │
│  │                              │      │
│  └──────────────────────────────┘      │
│                                        │
│  ┌──────────────────────────────┐      │
│  │      SALVAR NOVA SENHA       │      │
│  └──────────────────────────────┘      │
└────────────────────────────────────────┘
```

---

## 9. Controle de Acesso em Tempo de Execução

### 9.1 Verificação no Login

Ao logar com sucesso, o sistema carrega na sessão (JWT):

```
{
  "user_id": "uuid",
  "tenant_id": "uuid",
  "username": "matheus",
  "profile_id": "uuid",
  "profile_name": "Admin",
  "permissions": ["dashboard", "comandas", "compras", "estoque", "cadastros", "relatorios", "configuracoes", "gestao_usuarios"],
  "exp": 1747234567
}
```

### 9.2 Verificação em Cada Tela

Toda tela do sistema verifica a permissão antes de renderizar:

```
Usuário clica em "Relatórios" no menu lateral
    ↓
Frontend verifica: "relatorios" está em permissions[]?
    ↓
SIM → renderiza a tela
NÃO → mostra mensagem "Você não tem permissão para acessar esta área"
      e redireciona para tela anterior
```

### 9.3 Menu Lateral Dinâmico

O menu lateral mostra **apenas as opções permitidas** ao usuário logado.

**Exemplo — perfil Caixa (acesso a Dashboard, Comandas, Estoque):**

```
📊 Dashboard
🍺 Comandas
📦 Estoque
```

As outras opções (Compras, Cadastros, Relatórios, Configurações) **não aparecem** no menu.

**Por que ocultar e não desabilitar:**
- Menos confusão visual
- Usuário não se frustra tentando clicar em algo bloqueado
- Interface mais limpa para cada perfil

### 9.4 Proteção no Backend

**IMPORTANTE:** o frontend ocultar a tela é apenas UX. **O backend SEMPRE valida a permissão** antes de retornar qualquer dado.

```
Cliente faz request: GET /api/relatorios/dre
    ↓
Backend lê o JWT
    ↓
Verifica: usuário tem permissão "relatorios"?
    ↓
SIM → executa e retorna dados
NÃO → retorna 403 Forbidden
```

Isso previne acesso não autorizado mesmo se alguém manipular o frontend.

### 9.5 Mudança de Permissão em Tempo Real

Cenário: Admin remove a permissão "relatorios" do perfil "Caixa" enquanto João (caixa) está logado vendo um relatório.

**Comportamento:**
- A sessão atual de João **continua válida**
- Próxima requisição de João para uma rota de relatórios → backend retorna 403
- Frontend recebe 403 → faz logout automático ou redireciona com mensagem
- Toast: "Suas permissões foram alteradas. Por favor, faça login novamente."

---

## 10. Auditoria e Segurança

### 10.1 Logs de Acesso (opcional no MVP)

Eventos registrados na tabela `access_logs`:

| Evento | Quando |
|--------|--------|
| `login_success` | Login bem-sucedido |
| `login_failed` | Tentativa de login com credenciais inválidas |
| `logout` | Logout explícito |
| `password_reset_requested` | Solicitação de recuperação de senha |
| `password_reset_completed` | Senha alterada via link |
| `password_changed` | Senha alterada pelo próprio usuário |
| `access_denied` | Tentativa de acessar tela sem permissão |
| `user_created` | Novo usuário cadastrado |
| `user_updated` | Usuário editado |
| `user_deleted` | Usuário excluído |
| `profile_created` | Novo perfil criado |
| `profile_updated` | Perfil editado |
| `permission_changed` | Permissão alterada em perfil |

### 10.2 Boas Práticas de Segurança

| Prática | Implementação |
|---------|---------------|
| Senhas em hash | bcrypt com salt rounds 10 |
| Tokens JWT assinados | HMAC SHA-256 com secret seguro |
| HTTPS obrigatório | Em produção, todo o tráfego via TLS |
| Rate limiting no login | Máximo 5 tentativas por IP em 15 minutos |
| Token de reset com validade | 1 hora, uso único |
| Mensagens de erro genéricas | "Credenciais inválidas" — nunca revelar se usuário existe |
| Validação dupla (frontend + backend) | Frontend para UX, backend para segurança |
| Senhas nunca em logs | Logs nunca incluem campo de senha |
| Sessão expira | 8 horas de inatividade ou 12 horas absolutas |

### 10.3 Proteção Contra Ataques Comuns

**Brute force:**
- Rate limiting por IP no endpoint de login
- Bloqueio temporário após 5 tentativas falhas

**SQL Injection:**
- Uso de queries parametrizadas (ORM ou prepared statements)

**XSS:**
- Sanitização de inputs
- Escape de outputs em templates

**CSRF:**
- Tokens CSRF em formulários (se aplicável)
- SameSite cookies

---

## 11. Casos de Borda e Validações

### 11.1 Tabela de Casos

| Cenário | Comportamento esperado |
|---------|------------------------|
| Tentativa de excluir o único Admin | Bloqueia com toast vermelho: "Não é possível excluir o último administrador" |
| Tentativa de desativar a si mesmo | Bloqueia com toast: "Você não pode desativar sua própria conta" |
| Tentativa de mudar próprio perfil | Bloqueia. Apenas outro Admin pode alterar |
| Username já existe no tenant | Validação em tempo real: "Este usuário já existe" |
| Email já existe globalmente | Validação em tempo real: "Este email já está em uso" |
| Token de reset expirado | Tela: "Link expirado. Solicite um novo." |
| Token de reset já usado | Tela: "Link já utilizado. Solicite um novo se precisar." |
| Login com usuário desativado | Toast: "Usuário inativo. Procure o administrador." |
| Permissão revogada em sessão ativa | 403 na próxima requisição → logout automático com aviso |
| Tenant inativo (assinatura cancelada) | Bloqueia login com mensagem: "Acesso suspenso. Entre em contato com o suporte." |
| Exclusão de perfil com usuários vinculados | Modal: "X usuários têm este perfil. Escolha outro perfil para eles antes de excluir" |
| Senha muito curta | Validação inline: "Mínimo 6 caracteres" |
| Senhas não conferem (na confirmação) | Validação inline: "As senhas não coincidem" |

### 11.2 Estados Vazios

**Lista de usuários vazia (improvável, mas possível):**
- Mostrar mensagem amigável: "Nenhum usuário cadastrado além do Admin"
- CTA grande: "+ Cadastrar primeiro usuário"

**Lista de perfis com apenas os do sistema:**
- Mostrar normalmente, com CTA "+ Novo perfil" se quiser customizar

---

## 12. Roadmap Futuro

### Curto Prazo (pós-MVP)

- **Granularidade de permissões (view/edit/delete):** ao invés de só "pode acessar", separar em ações
- **Permissões em nível de funcionalidade:** ex: "pode aplicar desconto", "pode cancelar comanda"
- **Histórico de alterações de perfil:** quem mudou quais permissões e quando

### Médio Prazo

- **Two-Factor Authentication (2FA):** para Admin, via SMS ou app autenticador
- **SSO (Single Sign-On):** integração com Google, Microsoft
- **Política de senha forte:** exigir letras, números, símbolos
- **Expiração obrigatória de senha:** trocar a cada N dias

### Longo Prazo

- **Permissões por horário:** caixa só acessa entre 18h-2h
- **Permissões por valor:** garçom só aplica desconto até X%, acima precisa do Admin aprovar
- **Auditoria avançada:** dashboard de segurança com gráficos
- **Sessões simultâneas:** controle de quantas sessões um usuário pode ter ao mesmo tempo
- **Geofencing:** acesso apenas de IPs ou localizações específicas

---

## Histórico de Versões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 13/05/2026 | Equipe Flow4Tech | Documento inicial completo |
