# PRP — Issue #19: Cockpit consolidado
**GitHub Issue:** #19 | **Type:** HITL | **Depende de:** #13, #14

## Tarefas

### Bloco A — View SQL
- [ ] A1. Criar migration 0061 com CREATE OR REPLACE VIEW view_calendario_consolidado (PG only, UNION ALL 4 camadas)

### Bloco B — API
- [ ] B1. Schema cockpit.py — CockpitItem
- [ ] B2. Service cockpit_service.py — list_consolidado(db, mes, permissions) via ORM
- [ ] B3. Router cockpit.py — GET /api/calendario/consolidado?mes=YYYY-MM
- [ ] B4. Registrar router em main.py

### Bloco C — Frontend
- [ ] C1. useConsolidado.ts — React Query hook
- [ ] C2. CalendarioPage.tsx — adicionar conta_pagar + entrega_insumo layers + toggles + modals

### Bloco D — Testes
- [ ] D1. test_cockpit.py — usuário sem "financeiro" → sem conta_pagar
- [ ] D2. Usuário com todas as telas → 4 camadas presentes
- [ ] D3. Tenant isolation

## Validações
```bash
cd backend && source .venv/bin/activate && pytest
cd frontend && npm run type-check && npm run lint && npm run build
```
