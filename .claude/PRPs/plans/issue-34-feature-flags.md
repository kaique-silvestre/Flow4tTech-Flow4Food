# Issue #34 — Feature Flags por Tenant

## What already exists (from #25)
- Migration `0074_tenant_features`: `tenant_features(tenant_id, feature, enabled, updated_at)`
- `TenantFeature` model + `platform_repository.get/upsert_tenant_features`
- `GET /api/platform/tenants/:id/features` + `PUT /api/platform/tenants/:id/features`
- `FeaturesTab` in PlatformTenantDetailPage (but limited features + no PT-BR labels)

## What still needs to be built

### Backend
- [ ] `require_feature(key)` dependency in `dependencies.py` — 403 if row exists and enabled=false; no row = allowed
- [ ] `GET /api/app/features` in new `routes/features.py` — auth: `get_current_user`, returns `list[FeatureItem]` for tenant
- [ ] Register features route in `main.py`
- [ ] Add `Depends(require_feature("X"))` to routers:
  - dashboard.py → `dashboard`
  - eventos.py → `calendario`
  - comandas.py → `comandas`
  - consumo_interno.py → `consumo_interno`
  - compras.py → `compras`
  - estoque.py → `estoque`
  - relatorios.py → `relatorios`
  - categorias.py, fornecedores.py, garcons.py, insumos.py, metodos_pagamento.py, promocoes.py → `cadastros`
  - config.py → `configuracoes`
  - users.py, profiles.py → `gestao_usuarios` (add at router level)
  - contas_pagar.py → `financeiro`
- [ ] Tests for `GET /api/app/features` + `require_feature` 403 behavior

### Frontend
- [ ] Fix `AVAILABLE_FEATURES` in PlatformTenantDetailPage: all 11 modules + PT-BR labels dict + rename tab "Módulos"
- [ ] Add `feature?: string` to `NavItem`/`SubNavItem` in navConfig.ts + assign feature keys to NAV_ITEMS
- [ ] Create `frontend/src/hooks/useFeatureFlags.ts` — react-query fetch `GET /api/app/features`
- [ ] Update Sidebar.tsx to filter items by feature flags (in addition to permissions)

## Feature key → module mapping
| Feature key | Module |
|---|---|
| dashboard | Dashboard |
| calendario | Calendário |
| comandas | Vendas/Comandas |
| consumo_interno | Consumo Interno |
| compras | Compras/NF-e |
| estoque | Estoque |
| relatorios | Relatórios |
| cadastros | Cadastros |
| configuracoes | Configurações |
| gestao_usuarios | Gestão de Usuários |
| financeiro | Financeiro |

## Validations
- `cd backend && uv run ruff check --fix src/`
- `cd frontend && npm run type-check && npm run lint && npm run build`
