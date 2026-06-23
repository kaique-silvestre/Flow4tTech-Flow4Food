# Plan: Issue #29 — Cockpit de métricas por tenant

## Goal
Build `/platform/cockpit` page showing aggregated metrics per tenant, plus single-tenant endpoint.

## Acceptance Criteria
- [ ] A1: `platform_repository.get_cockpit_metrics()` — raw SQL, one query per tenant (no N+1)
- [ ] A2: `platform_repository.get_tenant_cockpit_metrics(tenant_id)` — same metrics for one tenant
- [ ] B1: `GET /api/platform/cockpit` endpoint in `platform_auth.py`
- [ ] B2: `GET /api/platform/tenants/{id}/cockpit` endpoint in `platform_auth.py`
- [ ] C1: `CockpitMetrics` Pydantic schema (inline in route file, like existing schemas)
- [ ] D1: `usePlatformCockpit` + `useTenantCockpit` hooks added to `usePlatformApi.ts`
- [ ] D2: `CockpitMetricsItem` TypeScript interface in `usePlatformApi.ts`
- [ ] E1: `PlatformCockpitPage.tsx` — table with sort + subscription filter
- [ ] F1: Route `/platform/cockpit` added to `App.tsx` inside `RequirePlatformAuth`
- [ ] F2: Nav link "Cockpit" added to `PlatformLayout.tsx`
- [ ] G1: Backend tests for cockpit endpoints

## Files to Touch
- `backend/src/repositories/platform_repository.py` — add 2 functions
- `backend/src/api/routes/platform_auth.py` — add 2 endpoints + schemas
- `frontend/src/features/platform/usePlatformApi.ts` — add hooks + interface
- `frontend/src/features/platform/PlatformCockpitPage.tsx` — NEW
- `frontend/src/features/platform/PlatformLayout.tsx` — add nav link
- `frontend/src/App.tsx` — add route

## SQL Strategy (no N+1)
Single query joining tenants → assinaturas → subqueries per metric:

```sql
SELECT
  t.id,
  t.nome_fantasia,
  t.cnpj,
  t.created_at,
  t.status                                          AS status_tenant,
  a.status                                          AS status_assinatura,
  EXTRACT(DAY FROM NOW() - t.created_at)::int       AS dias_cliente,
  (SELECT MAX(u.last_login)
   FROM system_users u WHERE u.tenant_id = t.id)   AS ultimo_login,
  (SELECT COUNT(*)
   FROM comandas c
   WHERE c.tenant_id = t.id
     AND DATE_TRUNC('month', c.created_at) = DATE_TRUNC('month', NOW()))
                                                    AS comandas_mes,
  (SELECT COALESCE(SUM(c.total), 0)
   FROM comandas c
   WHERE c.tenant_id = t.id
     AND c.status = 'fechada'
     AND DATE_TRUNC('month', c.created_at) = DATE_TRUNC('month', NOW()))
                                                    AS faturamento_mes,
  (SELECT COUNT(DISTINCT u.id)
   FROM system_users u
   WHERE u.tenant_id = t.id
     AND u.last_login >= NOW() - INTERVAL '30 days')
                                                    AS usuarios_ativos_30d,
  (SELECT COUNT(*)
   FROM compras cp
   WHERE cp.tenant_id = t.id
     AND DATE_TRUNC('month', cp.created_at) = DATE_TRUNC('month', NOW()))
                                                    AS compras_mes
FROM tenants t
LEFT JOIN assinaturas a ON a.tenant_id = t.id
ORDER BY t.id
```

For single tenant: same query + `WHERE t.id = :tenant_id`.

## Notes
- Platform engine has no RLS — can read all tenant data directly
- No migration needed (no new tables/columns)
- `from __future__ import annotations` is used in platform_repository.py — keep it
- Test: use platform engine SQLite like existing platform tests (if any exist), else mock DB
