# PRP Issue #33 — Tenant Detail: Aba Perfis e Permissões

## Context
Backend endpoints already implemented (from issue #25):
- `GET /api/platform/tenants/:id/profiles` — returns ProfileResponse with id, name, description, is_active, permissions[], user_count
- `PATCH /api/platform/tenants/:id/profiles/:pid` — accepts is_active and permissions[]

Frontend hook `useUpdateTenantProfile` already supports both fields.

## Tasks

### Task 1 — Update ProfileItem interface (usePlatformApi.ts)
Add missing `description: string | null` and `user_count: number` fields to `ProfileItem`.

File: `frontend/src/features/platform/usePlatformApi.ts` ~line 81

### Task 2 — Rewrite PerfisTab (PlatformTenantDetailPage.tsx)
Replace the stub `PerfisTab` with a full implementation:

**Table columns:** Nome | Descrição | Permissões (chips PT-BR) | Usuários | Status (badge) | Ações

**SCREENS constant (match ProfileModal.tsx):**
```
{ id: "dashboard", label: "Dashboard" }
{ id: "comandas", label: "Comandas / Cardápio" }
{ id: "compras", label: "Compras" }
{ id: "estoque", label: "Estoque" }
{ id: "cadastros", label: "Cadastros" }
{ id: "relatorios", label: "Relatórios" }
{ id: "configuracoes", label: "Configurações" }
{ id: "gestao_usuarios", label: "Gestão de Usuários" }
```

**Edit modal:** Opens on "Editar permissões" button. Checkboxes for each screen with PT-BR label. Save calls `updateProfile.mutate({ permissions: [...] })`.

**Toggle ativar/desativar:**
- When disabling (is_active → false) AND user_count > 0: show inline confirmation "X usuários vinculados. Confirmar desativação?"
- When activating or no users: toggle directly without confirmation
- Calls `updateProfile.mutate({ is_active: !p.is_active })`

**Permissions display (view mode):** chips with PT-BR labels (lookup from SCREENS), not raw IDs.

## Validations
- `npm run type-check` — zero errors
- `npm run lint` — zero errors  
- `npm run build` — success
- No backend tests to write (endpoints tested in issue #25)

## Acceptance Criteria (from issue)
- [x] Endpoint GET /api/platform/tenants/:id/profiles — already done
- [x] Endpoint PATCH /api/platform/tenants/:id/profiles/:pid — already done  
- [ ] Table: nome, descrição, permissões (chips), usuários vinculados, badge ativo/inativo
- [ ] Modal edição: checkboxes por módulo com labels PT-BR
- [ ] Toggle ativar/desativar com confirmação quando user_count > 0
- [ ] Labels PT-BR idênticos ao nav
