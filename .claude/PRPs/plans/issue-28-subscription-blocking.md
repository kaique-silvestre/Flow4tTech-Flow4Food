# Issue #28 — Bloqueio de Acesso por Status de Assinatura

## Objetivo
Dependência FastAPI que verifica `assinaturas.status` + `data_vencimento` a cada request autenticado de tenant. Se suspenso/cancelado/trial vencido → 402 com `SUBSCRIPTION_BLOCKED`. Frontend intercepta 402 globalmente (já existe em api.ts) e redireciona para `/blocked`.

## Acceptance Criteria
- [ ] A1. `CONTACT_EMAIL` em Settings config
- [ ] A2. `check_subscription` dep (DB real-time) em `dependencies.py` — usa `get_platform_db`
- [ ] A3. `get_tenant_db` depende de `check_subscription` (em vez de `get_current_user`) — cobre TODOS os tenant routers sem tocar cada arquivo
- [ ] B1. Teste: tenant `suspensa` → 402 com `SUBSCRIPTION_BLOCKED`
- [ ] B2. Teste: tenant `cancelada` → 402
- [ ] B3. Teste: trial com `data_vencimento < now` → 402
- [ ] B4. Teste: tenant `ativa` → 200
- [ ] C1. `api.ts` interceptor 402 → redireciona `/blocked?status=...&contact=...`
- [ ] C2. `BlockedPage.tsx` — lê query params, exibe status + contato
- [ ] C3. `App.tsx` — rota `/blocked` fora de RequireAuth

## Arquitetura

### Backend: check_subscription
```python
def check_subscription(
    platform_db: Session = Depends(get_platform_db),
    payload: dict = Depends(get_current_user),
) -> dict:
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        return payload
    assinatura = platform_db.query(Assinatura).filter(Assinatura.tenant_id == tenant_id).first()
    if assinatura is None:
        return payload
    now = datetime.now(timezone.utc)
    blocked = assinatura.status in {"suspensa", "cancelada"} or (
        assinatura.status == "trial"
        and assinatura.data_vencimento is not None
        and assinatura.data_vencimento.replace(tzinfo=timezone.utc) < now
    )
    if blocked:
        settings = get_settings()
        raise HTTPException(
            status_code=402,
            detail={"code": "SUBSCRIPTION_BLOCKED", "status": assinatura.status, "contact": settings.CONTACT_EMAIL},
        )
    return payload
```

### Backend: get_tenant_db (mudança mínima)
```python
def get_tenant_db(
    db: Session = Depends(get_db),
    payload: dict = Depends(check_subscription),  # era get_current_user
) -> Generator:
    ...
```

### Frontend: api.ts 402 handler
```ts
if (error.response?.status === 402) {
  const detail = (error.response.data as any)?.detail;
  const status = detail?.status ?? "suspensa";
  const contact = detail?.contact ?? "";
  const params = new URLSearchParams({ status, contact });
  if (window.location.pathname !== "/blocked") {
    window.location.assign(`/blocked?${params}`);
  }
  return Promise.reject(error);
}
```

## Arquivos a Modificar
- `backend/src/core/config.py` — add CONTACT_EMAIL
- `backend/src/api/dependencies.py` — update check_subscription + get_tenant_db
- `backend/tests/test_issue28_subscription_blocking.py` — NEW
- `frontend/src/lib/api.ts` — update 402 handler
- `frontend/src/features/assinatura/BlockedPage.tsx` — NEW
- `frontend/src/App.tsx` — add /blocked route

## Notas
- `get_platform_db` existe em `database.py` — sem RLS, sem checkout listener
- Auth routes usam `get_db` diretamente, não `get_tenant_db` → isentas automaticamente
- `require_active_subscription` existente (JWT-only) fica intacto — testes de billing existentes passam
- `data_vencimento` no model é `DateTime(timezone=True)` — can be naive or tz-aware; usar `.replace(tzinfo=timezone.utc)` defensivamente ou comparar via `astimezone`
