# Platform Admin — Redesign & Novas Funcionalidades

## Contexto

Painel em `/platform/*` usado pelos admins Flow4Tech para gerenciar tenants (empresas clientes).
Atualmente: layout minimalista (só header), tabela básica de tenants sem edição real.

---

## Identidade Visual

Sidebar igual à app normal (`bg-white border-r border-gray-200`), com navegação lateral.
Nav item único por ora: **Empresas** (`/platform/tenants`).
Header simplificado: logo + email do admin + botão Sair.

---

## Funcionalidades

### 1. Lista de Empresas (`/platform/tenants`)

**Adicionar colunas:**
- ID
- Nome Fantasia
- CNPJ
- Status Tenant
- Assinatura
- Vencimento
- Qtd. Usuários (`current / max`)

**Botão:** "Nova Empresa" → abre modal de criação.

**Modal Criar Empresa:**
- `nome_fantasia` (obrigatório)
- `cnpj`
- `endereco`
- `telefone`
- `max_users` (default 5)

---

### 2. Detalhe da Empresa (`/platform/tenants/:id`)

Página com **3 abas**: Dados | Usuários | Perfis

#### Aba: Dados
Formulário editável com todos os campos do tenant:
- `nome_fantasia`, `cnpj`, `endereco`, `telefone`
- `status` (ativo / inativo)
- `max_users`
- Campos read-only: ID, `created_at`
- Botão "Salvar"

#### Aba: Usuários
Tabela: Nome | Username | Email | Perfil | Último Login | Ativo

Ações:
- **Criar usuário** → modal com: `name`, `username`, `email`, `password`, `profile_id`, `is_active`
- **Editar usuário** → mesmo modal, senha opcional (vazio = não altera)
- **Ativar / Desativar** inline

Limite exibido: `X / max_users usuários ativos`

#### Aba: Perfis
Tabela: Nome | Descrição | Permissões | Usuários vinculados | Ativo

Ações:
- **Editar permissões** → modal com checkboxes por tela:
  ```
  dashboard, calendario, comandas, consumo_interno,
  compras, estoque, relatorios, cadastros,
  configuracoes, gestao_usuarios
  ```
- **Ativar / Desativar** perfil

---

## Backend — Novos Endpoints

Todos em `router` (requer `require_platform_admin`).
Prefixo: `/api/platform`

| Método | Path | Descrição |
|--------|------|-----------|
| `POST` | `/tenants` | Criar tenant |
| `GET` | `/tenants/{id}` | Detalhe do tenant |
| `PATCH` | `/tenants/{id}` | Atualizar tenant |
| `POST` | `/tenants/{id}/users` | Criar usuário |
| `PATCH` | `/tenants/{id}/users/{uid}` | Atualizar usuário |
| `GET` | `/tenants/{id}/profiles` | Listar perfis + permissões |
| `PATCH` | `/tenants/{id}/profiles/{pid}` | Atualizar perfil (is_active + screens) |

### Notas de implementação

- `POST /tenants` — cria `Tenant` + `Assinatura` (status `trial`) no mesmo commit
- `POST /tenants/{id}/users` — usa `hash_password` de `auth_service`; respeita `max_users`
- `PATCH /tenants/{id}/users/{uid}` — senha só altera se `password` vier no body
- `PATCH /tenants/{id}/profiles/{pid}` — reutiliza `profiles_repository.update_profile(screens)`; `is_active` atualizado separado
- Todos os queries no `platform_repository.py` usam conexão de superuser (já é o padrão do `get_platform_db`)
- RLS não se aplica aqui — plataforma acessa tudo sem `app.tenant_id`

---

## Frontend — Arquivos Afetados

| Arquivo | Mudança |
|---------|---------|
| `PlatformLayout.tsx` | Reescrever — adicionar sidebar |
| `PlatformTenantsPage.tsx` | Adicionar col ID, botão Nova Empresa, modal criar |
| `PlatformTenantDetailPage.tsx` | Reescrever completo — 3 abas |
| `usePlatformApi.ts` | Adicionar todos os hooks novos |

### Hooks novos em `usePlatformApi.ts`

```ts
useTenant(id)                    // GET /tenants/:id
useCreateTenant()                // POST /tenants
useUpdateTenant()                // PATCH /tenants/:id
useCreateTenantUser()            // POST /tenants/:id/users
useUpdateTenantUser()            // PATCH /tenants/:id/users/:uid
useTenantProfiles(id)            // GET /tenants/:id/profiles
useUpdateTenantProfile()         // PATCH /tenants/:id/profiles/:pid
```

---

## Ordem de Implementação

1. `platform_repository.py` — adicionar funções
2. `platform_auth.py` — adicionar endpoints + schemas Pydantic
3. `usePlatformApi.ts` — hooks novos
4. `PlatformLayout.tsx` — sidebar
5. `PlatformTenantsPage.tsx` — col ID + modal criar
6. `PlatformTenantDetailPage.tsx` — 3 abas completas
