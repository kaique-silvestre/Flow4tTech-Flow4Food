# Issue #31 — Detalhe do Tenant: Aba Dados & Assinatura

## Context

Issue #25 já construiu ~90% desta feature. Gaps restantes:

### Backend
1. `get_assinatura_history()` — JOIN com `platform_admins` p/ retornar `changed_by_name`
2. `AssinaturaHistoryItem` schema — adicionar `changed_by_name: Optional[str]`

### Frontend
3. `DadosTab` state — adicionar `cnpj`, `endereco`, `telefone`
4. `DadosTab` edit form — campos cnpj, endereco, telefone
5. `DadosTab` handleSave — passar cnpj/endereco/telefone ao mutate
6. `DadosTab` view mode — mostrar endereco, telefone (cnpj já existe)
7. `AssinaturaHistoryItem` type em `usePlatformApi.ts` — adicionar `changed_by_name: string | null`
8. History display — mostrar nome do admin responsável

## Files

- `backend/src/repositories/platform_repository.py` — fix history query (JOIN)
- `backend/src/api/routes/platform_auth.py` — fix `AssinaturaHistoryItem` schema
- `frontend/src/features/platform/usePlatformApi.ts` — fix `AssinaturaHistoryItem` type
- `frontend/src/features/platform/PlatformTenantDetailPage.tsx` — fix DadosTab

## Validations

```bash
cd backend && source .venv/bin/activate && python -m pytest tests/ -x -q 2>&1 | tail -20
cd frontend && npm run type-check 2>&1 | tail -20
cd frontend && npm run lint 2>&1 | tail -20
cd frontend && npm run build 2>&1 | tail -10
```
