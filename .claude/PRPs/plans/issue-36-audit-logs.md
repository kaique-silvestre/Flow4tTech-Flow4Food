# Issue #36 — feat(platform): log de auditoria global

## Tasks

- [x] Model AuditLog exists (backend/src/models/audit_logs.py)
- [x] Migration 0076_create_audit_logs.py exists
- [x] AuditLog imported in models/__init__.py
- [x] Frontend route /platform/audit exists (placeholder)
- [ ] Backend: audit_service.py com log() + log_background()
- [ ] Backend: platform_audit.py route GET /api/platform/audit-logs com filtros
- [ ] Backend: registrar router em main.py
- [ ] Backend: instrumentar create_user, update_user, delete_user (users.py route)
- [ ] Backend: instrumentar create_tenant, update_assinatura, update_assinatura_full, impersonate_user (platform_auth.py)
- [ ] Frontend: getAuditLogs() em usePlatformApi.ts
- [ ] Frontend: PlatformAuditPage.tsx implementado com tabela + filtros
- [ ] Tests: criar usuário durante impersonation → log com impersonated_by preenchido
- [ ] Commit

## Acceptance criteria
- audit_service.log_background() usa BackgroundTasks (non-blocking)
- GET /api/platform/audit-logs filtra por tenant_id, user_id, action, date_from, date_to, paginação
- Página /platform/audit: timestamp, tenant, usuário, ação, entidade, flag impersonation
- Filtros funcionais na página
