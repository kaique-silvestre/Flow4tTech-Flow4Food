# Documentação de Acessos — Flow4Food

> Documentação **executável** do sistema de autenticação, autorização e acessos.
> Esta doc foi escrita para ser **lida e executada pelo Claude do Cursor** com acesso aos dois repositórios:
> - `flow4tech-site` (Next.js + TypeScript)
> - `flow4food-app` (Python + FastAPI)
>
> Versão: 1.0 — 13/05/2026

---

## Como Usar Esta Documentação

Esta doc segue um padrão **agentic**: contém instruções de verificação, decisão e implementação que devem ser executadas em sequência por uma IA assistente no editor de código (Cursor ou Claude Code).

### Convenções

| Símbolo | Significado |
|---------|-------------|
| 🔍 **VERIFICAR** | Instrução para inspecionar arquivos/código existente |
| 📋 **REPORTAR** | O que a IA deve informar ao desenvolvedor humano |
| ⚙️ **IMPLEMENTAR** | Alteração de código a ser feita |
| ⚠️ **APROVAÇÃO HUMANA** | Ponto onde IA deve PARAR e esperar confirmação |
| ❓ **DECISÃO** | Ponto onde o humano decide o caminho |
| 📌 **NOTA** | Informação contextual importante |

### Setup Inicial

Antes de executar esta doc, garanta:

```
~/projetos/
├── flow4tech-site/      (repo do site Next.js)
├── flow4food-app/       (repo do sistema FastAPI)
└── docs/
    └── acessos-flow4food.md  (este arquivo)
```

Abra os 3 no mesmo workspace do Cursor.

---

## Índice

### PARTE 1 — Arquitetura
1. [Contexto e Decisões](#1-contexto-e-decisões)
2. [Arquitetura Cross-Domain](#2-arquitetura-cross-domain)

### PARTE 2 — Verificações
3. [Verificação da Stack do Sistema](#3-verificação-da-stack-do-sistema)
4. [Verificação da Autenticação Atual no Sistema](#4-verificação-da-autenticação-atual-no-sistema)
5. [Verificação da Tela de Login no Site](#5-verificação-da-tela-de-login-no-site)
6. [Verificação de CORS, Sessão e Cookies](#6-verificação-de-cors-sessão-e-cookies)

### PARTE 3 — Decisões
7. [Árvore de Decisões](#7-árvore-de-decisões)

### PARTE 4 — Migração
8. [Plano de Migração da Tela de Login](#8-plano-de-migração-da-tela-de-login)

### PARTE 5 — Sistema de Permissões
9. [Modelagem de Dados](#9-modelagem-de-dados)
10. [Regras de Negócio](#10-regras-de-negócio)
11. [Telas do Sistema](#11-telas-do-sistema)
12. [Controle de Acesso em Runtime](#12-controle-de-acesso-em-runtime)

### PARTE 6 — Recuperação de Senha
13. [Fluxo de Recuperação](#13-fluxo-de-recuperação)

### PARTE 7 — Auditoria e Segurança
14. [Auditoria e Segurança](#14-auditoria-e-segurança)

### PARTE 8 — Execução
15. [Roteiro de Execução](#15-roteiro-de-execução)

---

# PARTE 1 — ARQUITETURA

---

## 1. Contexto e Decisões

### Cenário

- **Site** (`flow4tech-site`): Next.js + TypeScript, hospedado em `flow4tech.com.br`. Possui tela de login visualmente completa, **sem lógica de autenticação**.
- **Sistema** (`flow4food-app`): Python + FastAPI, hospedado em `app.flow4tech.com.br`. Possui tela de login simples, **com lógica básica funcional**.

### Decisão Arquitetural Tomada

**Solução A: Tela de Login no Sistema (FastAPI)**

O site Next.js terá apenas um botão "Entrar" que redireciona para `app.flow4tech.com.br/login`. A tela de login mora no sistema FastAPI, com a lógica completa de autenticação.

**Estratégia:**
1. Migrar a aparência visual da tela de login do site (Next.js) para o sistema (FastAPI).
2. Manter a lógica de autenticação no sistema.
3. Site mantém **zero código de autenticação**.

### Por Que Essa Decisão

- Lógica sensível (senhas, JWT, sessão) fica em um único lugar
- Site não precisa de banco de dados
- Manutenção centralizada
- Padrão de mercado (Notion, Linear, Slack)

---

## 2. Arquitetura Cross-Domain

### Diagrama de Fluxo

```
                          ┌─────────────────────────┐
                          │  flow4tech.com.br       │
                          │  (Site Next.js)         │
                          │                         │
                          │  - Landing              │
                          │  - Planos               │
                          │  - Botão "Entrar"  ────┼──┐
                          │  - Sem banco de dados   │  │
                          │  - Sem autenticação     │  │ Redirect
                          └─────────────────────────┘  │
                                                       │
                          ┌─────────────────────────┐  │
                          │  app.flow4tech.com.br   │◄─┘
                          │  (Sistema FastAPI)      │
                          │                         │
                          │  - /login (tela)        │
                          │  - /auth/* (endpoints)  │
                          │  - Banco de dados       │
                          │  - JWT + sessão         │
                          │  - Permissões           │
                          └─────────────────────────┘
```

### Configuração de DNS

Ambos os domínios devem apontar para servidores diferentes (ou subdomínio):

```
flow4tech.com.br          → Hospedagem do site (ex: Vercel)
app.flow4tech.com.br      → Hospedagem do sistema (ex: Railway, Render)
```

### Implementação do Redirect no Site

📌 **NOTA:** No site Next.js, o botão "Entrar" é simplesmente um link HTML. Nenhuma lógica de autenticação.

```tsx
// Exemplo no Next.js (header ou onde for o botão)
<Link href="https://app.flow4tech.com.br/login">
  Entrar
</Link>
```

🔍 **VERIFICAR:** No repo `flow4tech-site`, encontre o componente do header ou onde está o botão "Entrar" / "Meu acesso". Verifique se ele já faz redirect externo ou se aponta para rota interna.

📋 **REPORTAR:**
- Caminho do arquivo onde está o botão
- Para onde ele aponta atualmente
- Se precisa ser alterado para `https://app.flow4tech.com.br/login`

⚠️ **APROVAÇÃO HUMANA:** Antes de alterar, mostre o trecho atual e a alteração proposta.

---

# PARTE 2 — VERIFICAÇÕES NO CÓDIGO

> Esta parte é executada pelo Claude do Cursor com acesso aos dois repositórios. Cada seção contém instruções concretas de inspeção.

---

## 3. Verificação da Stack do Sistema

🔍 **VERIFICAR no repo `flow4food-app`:**

### 3.1 Arquivo de dependências

- Existe `requirements.txt`, `pyproject.toml`, ou `Pipfile`?
- Quais dependências estão listadas? Especialmente:
  - `fastapi` (confirma framework principal)
  - `jinja2` (templates HTML server-side)
  - `python-multipart` (form data)
  - `passlib`, `bcrypt` (hash de senha)
  - `python-jose` ou `pyjwt` (JWT)
  - `sqlalchemy`, `tortoise-orm`, `prisma` (ORM)
  - `alembic` (migrations)
  - `python-decouple`, `pydantic-settings` (env vars)

### 3.2 Estrutura de pastas

- Estrutura geral do projeto (ex: `app/`, `src/`, `core/`?)
- Existe pasta `templates/`? (indica uso de Jinja2 / SSR)
- Existe pasta `static/` ou `public/`?
- Existe pasta separada de frontend (`frontend/`, `client/`, `ui/`)?

### 3.3 Arquivo principal

- Encontre `main.py` ou equivalente
- Verifique como o FastAPI é instanciado
- Verifique se há `Jinja2Templates(directory=...)` configurado
- Verifique rotas atualmente registradas

📋 **REPORTAR:**

```
STACK DETECTADA:
- Framework: FastAPI [✅/❌]
- Templates: [Jinja2 / nenhum / outro: ___]
- Frontend: [server-side (Jinja2) / separado (qual?) / SPA no mesmo repo]
- ORM: [SQLAlchemy / Tortoise / Prisma / outro / não detectado]
- Auth atual: [bibliotecas detectadas]

ESTRUTURA DE PASTAS:
[árvore resumida]

ROTAS EXISTENTES RELACIONADAS A AUTH:
[listar rotas /login, /auth/*, etc.]
```

⚠️ **APROVAÇÃO HUMANA:** Pare aqui. Apresente o relatório e aguarde confirmação antes de prosseguir para a próxima verificação.

---

## 4. Verificação da Autenticação Atual no Sistema

🔍 **VERIFICAR no repo `flow4food-app`:**

### 4.1 Tela de login existente

- Encontre o template/componente da tela de login atual
- Capture o conteúdo completo
- Identifique:
  - Estrutura HTML/template
  - Estilos aplicados (CSS, classes Tailwind, framework)
  - Campos do formulário (email? username? ambos?)
  - Botão de submit
  - Link de "esqueci senha" (existe?)
  - Tratamento de erro visual

### 4.2 Endpoint de login

- Encontre a rota POST de login
- Identifique:
  - Como recebe credenciais (form, JSON, query)
  - Como busca usuário no banco
  - Como compara senha (bcrypt? texto puro? outro?)
  - O que retorna em caso de sucesso (JWT? cookie? sessão?)
  - O que retorna em caso de falha
  - Validações aplicadas

### 4.3 Modelo de usuário

- Encontre o modelo `User` (ou equivalente)
- Liste os campos atuais
- Verifique se há campos para:
  - `id`, `email`, `username`, `password_hash`
  - `is_active`, `tenant_id`, `profile_id`
  - `created_at`, `updated_at`, `last_login`

### 4.4 Middleware de autenticação

- Existe middleware que protege rotas?
- Como ele verifica a sessão/token?
- Como expõe o usuário atual para as rotas?

📋 **REPORTAR:**

```
TELA DE LOGIN ATUAL:
- Caminho: ___
- Tecnologia: [Jinja2 / outro]
- Visual atual: [descrição breve]
- Campos: [email / username / ambos]

LÓGICA DE LOGIN ATUAL:
- Endpoint: [método + caminho]
- Hash de senha: [bcrypt / outro / ❌ texto puro]
- Retorno em sucesso: [JWT / cookie / sessão]
- Validações: [listar]

MODELO USER:
- Campos atuais: [listar]
- Campos faltantes (vs documentação): [listar]

MIDDLEWARE:
- Existe: [sim/não]
- Funcionamento: [breve descrição]

⚠️ GAPS DETECTADOS:
[lista de problemas que precisam ser corrigidos]
```

⚠️ **APROVAÇÃO HUMANA:** Apresente o relatório completo e aguarde decisão sobre quais gaps corrigir.

---

## 5. Verificação da Tela de Login no Site

🔍 **VERIFICAR no repo `flow4tech-site`:**

### 5.1 Localização da tela

- Encontre a tela de login (provavelmente em `app/login/page.tsx` ou similar)
- Capture o código completo

### 5.2 Análise visual

Identifique:
- **Layout:** centralizado, dividido, full-screen?
- **Cores:** quais cores usa (referência ao design system do site)?
- **Tipografia:** quais fontes?
- **Espaçamento:** padding, margin, gap
- **Componentes usados:** inputs, botões, labels, ícones
- **Estados visuais:** focus, hover, erro, loading
- **Animações:** transições, efeitos
- **Responsividade:** breakpoints

### 5.3 Bibliotecas e componentes

- Component library? (shadcn/ui, Radix, MUI, Chakra?)
- Form library? (react-hook-form, formik?)
- Validação? (Zod, Yup?)
- Tailwind ou CSS modules?
- Ícones? (lucide-react, react-icons?)

### 5.4 Estrutura do formulário

- Campos exatos (nome, placeholder, tipo)
- Validações no frontend
- Tratamento de erro visual
- Botão de submit e estados
- Links auxiliares ("esqueci senha", "criar conta")

📋 **REPORTAR:**

```
TELA DE LOGIN NO SITE:
- Caminho: ___
- Layout: [descrição]
- Cores principais: [lista hex]
- Tipografia: [fontes usadas]

BIBLIOTECAS:
- UI: [shadcn / outro / nenhum]
- Forms: [react-hook-form / outro / nenhum]
- Validação: [zod / outro / nenhum]
- Estilo: [tailwind / outro]

COMPONENTES DA TELA:
[listar com descrição visual]

PORTABILIDADE PARA JINJA2:
- HTML estrutura: [✅ direto / ⚠️ adaptação necessária]
- Classes Tailwind: [✅ direto / ❌ não]
- Componentes React específicos: [listar o que precisa reescrever]
- Lógica JS interativa: [listar o que precisa traduzir]
```

📌 **NOTA:** Se o sistema usar Jinja2 (SSR), o HTML/CSS é portável quase 100%. JavaScript interativo precisará ser reescrito ou usado via `<script>` puro.

---

## 6. Verificação de CORS, Sessão e Cookies

🔍 **VERIFICAR no repo `flow4food-app`:**

### 6.1 Configuração de CORS

- Existe configuração de CORS no FastAPI?
- Quais origens são permitidas?
- A origem do site (`https://flow4tech.com.br`) está incluída?
- `allow_credentials=True`?

### 6.2 Configuração de cookies de sessão

- Como sessão é gerenciada?
- Se usa cookies, qual configuração?
  - `httpOnly`?
  - `secure`?
  - `samesite`?
  - `domain` configurado para subdomínio compartilhado?

### 6.3 Configuração de JWT

- Onde a chave secreta vem? (env var? hardcoded?)
- Algoritmo de assinatura?
- Tempo de expiração?
- Refresh token implementado?

📋 **REPORTAR:**

```
CORS:
- Configurado: [sim/não]
- Origens permitidas: [lista]
- Credenciais: [permitidas/não]
- ⚠️ Precisa adicionar: [listar origens faltantes]

COOKIES:
- Como gerenciados: ___
- HttpOnly: [sim/não]
- Secure: [sim/não]
- SameSite: [strict/lax/none/não definido]
- Domain: ___
- ⚠️ Recomendações: [listar]

JWT:
- Chave secreta: [env var / ⚠️ hardcoded]
- Algoritmo: [HS256 / outro]
- Expiração: ___
- Refresh: [implementado / não]
- ⚠️ Recomendações: [listar]
```

📌 **NOTA:** Cross-domain entre `flow4tech.com.br` e `app.flow4tech.com.br` exige configuração cuidadosa de CORS e cookies. Cookies com `domain=.flow4tech.com.br` funcionam para ambos.

---

# PARTE 3 — DECISÕES

---

## 7. Árvore de Decisões

Com base nos relatórios das Verificações 3-6, decidir os próximos passos.

### Decisão 1 — Estratégia de Frontend do Sistema

❓ **DECISÃO:** O sistema usa Jinja2 (server-side rendering) ou frontend separado?

**Se Jinja2:**
- ✅ A migração visual do site é viável com adaptação
- Plano: portar HTML/CSS, reescrever JS interativo
- Seguir Seção 8.1

**Se frontend separado (React/Vue/outro no repo):**
- ✅ Pode copiar componente quase direto
- Plano: traduzir tipos TypeScript, ajustar imports, conectar à API FastAPI
- Seguir Seção 8.2

**Se não tem frontend ainda (só API):**
- ⚠️ Decisão estratégica grande
- Opção A: adicionar Jinja2 ao FastAPI
- Opção B: criar frontend separado (provavelmente Next.js, reaproveitando o do site)
- Recomendação: **Opção A** para MVP. Mais simples e rápido.

### Decisão 2 — Tratar gaps críticos detectados

❓ **DECISÃO:** Quais gaps tratar agora?

Lista de gaps possíveis (a serem confirmados nas verificações):

| Gap | Severidade | Recomendação |
|-----|-----------|--------------|
| Senha em texto puro | 🔴 Crítico | Corrigir imediatamente (bcrypt) |
| Sem hash bcrypt | 🔴 Crítico | Adicionar |
| JWT sem expiração | 🔴 Crítico | Definir 8-14h |
| CORS não configurado para o site | 🔴 Crítico | Adicionar `https://flow4tech.com.br` |
| Modelo User sem `tenant_id` | 🟡 Importante | Adicionar (multi-tenant) |
| Modelo User sem `profile_id` | 🟡 Importante | Adicionar (permissões) |
| Sem middleware de auth | 🟡 Importante | Criar |
| Sem recuperação de senha | 🟡 Importante | Implementar (Seção 13) |

⚠️ **APROVAÇÃO HUMANA:** Apresente a lista de gaps detectados e pergunte ao humano quais tratar nesta sprint.

---

# PARTE 4 — MIGRAÇÃO

---

## 8. Plano de Migração da Tela de Login

### 8.1 Cenário: Sistema com Jinja2

Aplica-se se a Decisão 1 = Jinja2.

#### Passo 1 — Setup de Jinja2 (se não tiver)

🔍 **VERIFICAR:** `Jinja2Templates` configurado em `main.py`?

⚙️ **IMPLEMENTAR (se não tiver):**

```python
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
```

Criar pastas:
- `templates/`
- `static/css/`
- `static/js/`

#### Passo 2 — Extrair design da tela do site

Da Verificação 5, capturar:
- HTML estrutural
- Classes CSS (Tailwind)
- Cores, espaçamentos, fontes

⚙️ **IMPLEMENTAR:** Criar `templates/auth/login.html` com:

- Estrutura HTML idêntica à do site
- Classes Tailwind preservadas
- Substituir lógica React por:
  - `<form method="POST" action="/auth/login">`
  - Validação HTML5 nativa (`required`, `type="email"`)
  - Mensagens de erro vindas do backend via Jinja: `{% if error %}{{ error }}{% endif %}`

#### Passo 3 — Setup do Tailwind no FastAPI

📌 **NOTA:** Tailwind pode ser usado de duas formas:

**Opção A — CDN (mais rápido, MVP):**
```html
<script src="https://cdn.tailwindcss.com"></script>
```

**Opção B — Build local (produção):**
- Instalar Tailwind via npm dentro do projeto Python
- Configurar build watching as classes nos templates
- Mais trabalho, melhor performance

Recomendação MVP: **Opção A**, migrar para B depois.

#### Passo 4 — Endpoint do FastAPI

⚙️ **IMPLEMENTAR:**

```python
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "error": None
    })

@app.post("/auth/login")
async def login_submit(
    request: Request,
    email_or_username: str = Form(...),
    password: str = Form(...)
):
    user = await authenticate_user(email_or_username, password)
    if not user:
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": "Credenciais inválidas"
        })
    
    # Criar JWT, setar cookie, redirecionar
    token = create_jwt(user)
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        domain=".flow4tech.com.br",  # cross-subdomain
        max_age=14*3600  # 14 horas
    )
    return response
```

⚠️ **APROVAÇÃO HUMANA:** Antes de criar os arquivos, apresente o plano completo e aguarde aprovação.

### 8.2 Cenário: Sistema com Frontend Separado

Aplica-se se a Decisão 1 = frontend separado.

Caso o sistema tenha um frontend React/Vue/outro:

⚙️ **IMPLEMENTAR:**
1. Copiar o componente de login do site
2. Adaptar imports (caminhos podem ser diferentes)
3. Substituir mock por chamada real à API FastAPI
4. Ajustar tratamento de resposta (token, redirecionamento)

---

# PARTE 5 — SISTEMA DE PERMISSÕES

---

## 9. Modelagem de Dados

📌 **NOTA:** Esta seção integra a doc de permissões anterior, com correções dos gaps identificados.

### Tabelas

🔍 **VERIFICAR:** As tabelas abaixo já existem no banco? Use a Verificação 4 e o modelo `User` como referência.

#### Tabela: `tenants`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único |
| `name` | varchar(100) | Nome do estabelecimento |
| `is_active` | boolean | Tenant ativo (assinatura válida) |
| `created_at` | timestamp | Criação |
| `updated_at` | timestamp | Última atualização |

#### Tabela: `profiles`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único |
| `tenant_id` | UUID | Tenant dono do perfil |
| `name` | varchar(50) | Nome do perfil |
| `description` | text | Descrição opcional |
| `is_system` | boolean | Perfil do sistema (não excluível) |
| `created_at` | timestamp | Criação |
| `updated_at` | timestamp | Última atualização |

#### Tabela: `permissions`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único |
| `profile_id` | UUID | Referência ao perfil |
| `screen` | varchar(50) | Identificador da tela |
| `can_access` | boolean | Pode acessar? |

#### Tabela: `users`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único |
| `tenant_id` | UUID | Tenant do usuário |
| `profile_id` | UUID | Perfil atribuído |
| `name` | varchar(100) | Nome completo |
| `username` | varchar(50) | Login curto |
| `email` | varchar(150) | Email para recuperação |
| `password_hash` | varchar(255) | Hash bcrypt |
| `is_active` | boolean | Usuário ativo |
| `must_change_password` | boolean | Forçar troca no próximo login |
| `last_login` | timestamp | Último login bem-sucedido |
| `created_at` | timestamp | Criação |
| `updated_at` | timestamp | Última atualização |

#### Tabela: `password_resets`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único |
| `user_id` | UUID | Referência ao usuário |
| `token` | varchar(255) | Token único |
| `expires_at` | timestamp | Validade (1h) |
| `used_at` | timestamp | Quando foi usado |
| `created_at` | timestamp | Criação |

### Correções Aplicadas (vs doc anterior)

📌 **Email único POR TENANT** (não global). Permite que a mesma pessoa tenha conta em dois estabelecimentos. Constraint:
```sql
UNIQUE (tenant_id, email)
UNIQUE (tenant_id, username)
```

📌 **Login apenas por EMAIL** (sem ambiguidade de username cross-tenant). Username serve como identificador visual interno, não para login.

📌 **Campo `must_change_password`** adicionado para forçar troca no primeiro acesso (após criação por Admin).

⚙️ **IMPLEMENTAR:**
- Criar migrations Alembic (ou equivalente) para criar/ajustar tabelas
- Gerar modelos SQLAlchemy/ORM correspondentes
- Aplicar migrations

⚠️ **APROVAÇÃO HUMANA:** Antes de executar migrations no banco, apresente os scripts.

---

## 10. Regras de Negócio

### 10.1 Proteção do Perfil Admin

- Perfil `Admin` tem `is_system: true`
- **Não pode ser excluído**
- **Não pode ter nome alterado**
- **Não pode ter permissões alteradas** (sempre tem acesso a tudo)

### 10.2 Garantia de pelo menos 1 Admin ativo

Bloquear:
- Excluir o último Admin
- Desativar o último Admin
- Mudar o perfil do último Admin

### 10.3 Auto-edição

**Pode:** editar próprio nome, email, senha
**Não pode:** mudar próprio perfil, desativar a si mesmo, excluir a si mesmo

### 10.4 Unicidade

- `email` único POR TENANT
- `username` único POR TENANT

### 10.5 Senhas

- Mínimo: 6 caracteres
- Hash: bcrypt (salt rounds = 10)
- Nunca armazenar texto puro
- Nunca retornar em respostas de API

### 10.6 Sessão

- Duração: 14 horas absolutas (cobre operação de bar até madrugada)
- Renovação automática a cada requisição (sliding session)
- Expiração por inatividade: 4 horas

### 10.7 Mudança de Email

**Risco:** atacante muda email e usa "esqueci senha" para tomar conta.

**Mitigação:**
- Mudança de email requer **confirmação no email atual** antes de aplicar
- Notificação enviada para ambos os emails (antigo e novo)

### 10.8 Criação do Primeiro Admin

📌 **Fluxo de provisão de novo tenant:**

```
1. Cliente paga assinatura (webhook Asaas)
2. Sistema cria registro em `tenants`
3. Sistema cria perfis padrão (Admin, Caixa, Gerente)
4. Sistema cria usuário com profile = Admin, email = email do cliente
5. Senha = null, must_change_password = true
6. Sistema envia email de "definir senha" com token
7. Cliente clica → define senha → loga
```

⚙️ **IMPLEMENTAR:** Endpoint de webhook + lógica de provisionamento.

---

## 11. Telas do Sistema

🔍 **VERIFICAR:** Quais dessas telas já existem no sistema?

| Tela | Caminho sugerido | Existe? |
|------|------------------|---------|
| Login | `/login` | Verificar |
| Esqueci senha | `/esqueci-senha` | Verificar |
| Definir nova senha | `/redefinir-senha?token=X` | Verificar |
| Criar senha (primeiro acesso) | `/criar-senha?token=X` | Verificar |
| Gestão de usuários | `/configuracoes/usuarios` | Verificar |
| Cadastro/edição de usuário | (modal ou rota) | Verificar |
| Gestão de perfis | `/configuracoes/perfis` | Verificar |
| Edição de perfil/permissões | (modal ou rota) | Verificar |
| Alterar própria senha | `/minha-conta/senha` | Verificar |

📋 **REPORTAR:** Lista do que existe vs. falta.

⚙️ **IMPLEMENTAR:** Para cada tela faltante, criar template + endpoint seguindo o padrão visual da tela de login migrada.

📌 **NOTA:** Os wireframes detalhados de cada tela estavam na doc anterior (`permissoes-flow4food.md`). Reaproveitar.

---

## 12. Controle de Acesso em Runtime

### 12.1 Middleware de Autenticação

⚙️ **IMPLEMENTAR (se não existir):**

```python
from fastapi import Depends, HTTPException, Request
from jose import jwt

async def get_current_user(request: Request):
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        user = await load_user(payload["user_id"])
        if not user or not user.is_active:
            raise HTTPException(status_code=401)
        return user
    except:
        raise HTTPException(status_code=401)
```

### 12.2 Middleware de Autorização

⚙️ **IMPLEMENTAR:**

```python
def require_permission(screen: str):
    async def check(user = Depends(get_current_user)):
        permissions = await load_permissions(user.profile_id)
        if screen not in permissions:
            raise HTTPException(status_code=403, detail="Sem permissão")
        return user
    return check

# Uso em rotas:
@app.get("/relatorios")
async def relatorios(user = Depends(require_permission("relatorios"))):
    ...
```

### 12.3 Menu Lateral Dinâmico

🔍 **VERIFICAR:** Como o menu é renderizado hoje?

⚙️ **IMPLEMENTAR:** Menu deve mostrar **apenas itens com permissão** do usuário logado.

```html
{% if "dashboard" in user_permissions %}
  <a href="/dashboard">📊 Dashboard</a>
{% endif %}
{% if "comandas" in user_permissions %}
  <a href="/comandas">🍺 Comandas</a>
{% endif %}
```

### 12.4 Mudança de Permissão em Sessão Ativa

- Sessão atual continua válida
- Próxima requisição para rota proibida → 403
- Frontend redireciona ou desloga com toast
- Mensagem: "Suas permissões foram alteradas. Faça login novamente."

---

# PARTE 6 — RECUPERAÇÃO DE SENHA

---

## 13. Fluxo de Recuperação

### 13.1 Tela "Esqueci minha senha"

⚙️ **IMPLEMENTAR:**

Tela com único campo: email.

Ao submeter:
1. Buscar usuário pelo email
2. **Se encontrou:**
   - Invalidar tokens anteriores deste usuário
   - Gerar novo token (UUID)
   - Salvar em `password_resets` com `expires_at = now() + 1h`
   - Enviar email com link: `app.flow4tech.com.br/redefinir-senha?token=X`
3. **Se NÃO encontrou:**
   - Retornar a MESMA mensagem de sucesso (não vazar se email existe)

### 13.2 Email de Recuperação

```
Assunto: Recuperação de senha — Flow4Food

Olá [Nome],

Recebemos uma solicitação para redefinir sua senha.

Clique no link abaixo para criar uma nova senha:
[Botão: Redefinir minha senha]

Este link é válido por 1 hora.

Se você não solicitou esta alteração, ignore este email.

Equipe Flow4Tech
```

### 13.3 Tela "Redefinir senha"

Acessada via link do email.

Ao carregar:
1. Validar token (existe? não expirou? não foi usado?)
2. Se inválido: mostrar "Link expirado ou inválido. Solicite um novo."
3. Se válido: mostrar formulário com:
   - Nova senha
   - Confirmar nova senha

Ao submeter:
1. Validar senhas iguais
2. Hash bcrypt da nova senha
3. Atualizar `users.password_hash`
4. Marcar `password_resets.used_at = now()`
5. Invalidar TODAS as sessões ativas deste usuário
6. Redirecionar para login com toast "Senha redefinida"

### 13.4 Service de Email

🔍 **VERIFICAR:** Existe configuração de envio de email no sistema?

📌 **NOTA:** Você já tem Resend configurado no site Next.js. Pode reaproveitar a API key para o sistema FastAPI.

⚙️ **IMPLEMENTAR (se não existir):**
- Adicionar lib de envio (ex: `resend` para Python)
- Configurar API key via env var
- Criar service `EmailService` com métodos:
  - `send_password_reset(user, token)`
  - `send_welcome(user)`
  - `send_first_password(user, token)`

---

# PARTE 7 — AUDITORIA E SEGURANÇA

---

## 14. Auditoria e Segurança

### 14.1 Logs de Acesso

⚙️ **IMPLEMENTAR (opcional MVP):** Tabela `access_logs`.

Eventos a registrar:

| Evento | Quando |
|--------|--------|
| `login_success` | Login bem-sucedido |
| `login_failed` | Credenciais inválidas |
| `logout` | Logout explícito |
| `password_reset_requested` | Solicitação de recuperação |
| `password_reset_completed` | Senha alterada via link |
| `password_changed` | Usuário alterou própria senha |
| `access_denied` | Tentativa de acesso negado |
| `user_created` | Novo usuário cadastrado |
| `user_updated` | Usuário editado |
| `user_deleted` | Usuário excluído |
| `profile_updated` | Perfil editado |
| `permission_changed` | Permissão alterada |

### 14.2 Práticas Obrigatórias

| Prática | Implementação |
|---------|---------------|
| Senhas em hash | bcrypt (rounds=10) |
| JWT assinado | HS256 com chave em env var |
| HTTPS obrigatório | TLS em produção |
| Rate limiting no login | Máx 5 tentativas/15min por IP |
| Token reset com validade | 1h, uso único |
| Mensagens de erro genéricas | "Credenciais inválidas" |
| Validação dupla | Frontend (UX) + Backend (segurança) |
| Senhas nunca em logs | Filtrar campos sensíveis |
| Cookies HttpOnly | Sempre |
| Cookies Secure | Em produção |
| SameSite | `lax` para cross-domain mesmo site |

### 14.3 Configuração de CORS Necessária

⚙️ **IMPLEMENTAR:**

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://flow4tech.com.br",
        "https://app.flow4tech.com.br",
        "http://localhost:3000",  # dev do site
        "http://localhost:8000",  # dev do sistema
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 14.4 Configuração de Cookie para Cross-Subdomain

⚙️ **IMPLEMENTAR:** Ao setar cookie de sessão, usar `domain=".flow4tech.com.br"`:

```python
response.set_cookie(
    key="session",
    value=token,
    httponly=True,
    secure=True,
    samesite="lax",
    domain=".flow4tech.com.br",  # válido em todos os subdomínios
    max_age=14*3600
)
```

📌 **NOTA:** O ponto na frente (`.flow4tech.com.br`) é importante. Permite que o cookie seja válido em `flow4tech.com.br`, `app.flow4tech.com.br`, `admin.flow4tech.com.br`, etc.

---

# PARTE 8 — ROTEIRO DE EXECUÇÃO

---

## 15. Roteiro de Execução

Esta é a sequência sugerida de execução desta documentação pelo Claude do Cursor.

### Fase 1 — Mapeamento (sem mudanças no código)

Executar e reportar:
- [ ] Seção 3 — Verificação da Stack do Sistema
- [ ] Seção 4 — Verificação da Autenticação Atual no Sistema
- [ ] Seção 5 — Verificação da Tela de Login no Site
- [ ] Seção 6 — Verificação de CORS, Sessão e Cookies

📋 **REPORTAR:** Relatório consolidado de tudo que foi encontrado.

⚠️ **APROVAÇÃO HUMANA:** Esperar humano confirmar antes de qualquer mudança.

### Fase 2 — Decisões

- [ ] Seção 7 — Apresentar árvore de decisões com base no relatório
- [ ] Aguardar humano decidir caminhos

### Fase 3 — Implementação da Autenticação

Em ordem:
- [ ] 14.3 — Configurar CORS corretamente
- [ ] 14.4 — Configurar cookie cross-subdomain
- [ ] 9 — Aplicar correções no modelo de dados (migrations)
- [ ] 10.5 — Garantir hash bcrypt
- [ ] 12.1 — Criar middleware de autenticação
- [ ] 12.2 — Criar middleware de autorização

⚠️ **APROVAÇÃO HUMANA:** Antes de cada mudança significativa.

### Fase 4 — Migração da Tela de Login

- [ ] 8.1 ou 8.2 — Migrar tela conforme estratégia decidida
- [ ] Testar fluxo completo: site → click "Entrar" → login no sistema → dashboard

### Fase 5 — Recuperação de Senha

- [ ] 13 — Implementar fluxo completo de "esqueci senha"
- [ ] Configurar service de email (Resend)

### Fase 6 — Telas de Gestão de Usuários e Perfis

- [ ] 11 — Implementar telas faltantes seguindo padrão visual

### Fase 7 — Auditoria

- [ ] 14.1 — Implementar logs de acesso (se decidido)
- [ ] 14.2 — Validar todas as práticas de segurança

### Fase 8 — Atualização do Site

- [ ] 2 — Atualizar botão "Entrar" no site para redirecionar para `app.flow4tech.com.br/login`
- [ ] Remover qualquer lógica de autenticação residual do site

---

## Histórico de Versões

| Versão | Data | Mudanças |
|--------|------|----------|
| 1.0 | 13/05/2026 | Documento inicial — arquitetura agentic com verificações executáveis |
