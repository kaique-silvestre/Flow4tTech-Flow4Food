# PRP — Issue #2: get_db injection + correção de concorrência

**Parent Issues doc:** `docs/issues/issues_v1_lancamento_comercial.md` → Issue 2
**Type:** AFK
**Blocked by:** Issue 1 ✓ (completo)
**Status:** Em execução
**Criado em:** 2026-05-28

---

## Objetivo

Dois trabalhos acoplados:
1. **get_db injection** — `get_tenant_db` executa `SET LOCAL app.tenant_id` antes de qualquer query, lendo do JWT.
2. **Correção de concorrência** — SELECT FOR UPDATE em reserva de estoque + CAS `increment_version` em `aplicar_desconto` e `cancelar_comanda`.

---

## Tarefas

### Bloco A — get_db injection

- [ ] **A1.** `dependencies.py`: criar `get_tenant_db(db=Depends(get_db), payload=Depends(get_current_user))` que executa `SET LOCAL app.tenant_id` se DATABASE_URL começa com "postgresql".
- [ ] **A2.** Substituir `get_db` por `get_tenant_db` nas rotas operacionais (comandas, produtos, categorias, fornecedores, insumos, compras, estoque, pagamentos, garcons).

### Bloco B — Concorrência: SELECT FOR UPDATE

- [ ] **B1.** `estoque_repository.get_insumo_for_update`: adicionar `.with_for_update()` ao select.
- [ ] **B2.** `_reservar_estoque` em `comandas_service.py`: substituir `db.execute(select(Insumo)...)` por `estoque_repository.get_insumo_for_update(db, comp.insumo_id)`.
- [ ] **B3.** `_baixar_insumo` em `comandas_service.py`: usar `get_insumo_for_update` via parâmetro já passado.

### Bloco C — CAS: aplicar_desconto

- [ ] **C1.** `schemas/fechamento.py`: adicionar `version: int` a `AplicarDescontoRequest`.
- [ ] **C2.** `services/comandas_service.py`: `aplicar_desconto` chama `increment_version` → raise 409 se version stale.

### Bloco D — CAS: cancelar_comanda

- [ ] **D1.** `schemas/comandas.py`: criar `CancelarComandaRequest(version: int)`.
- [ ] **D2.** `services/comandas_service.py`: `cancelar_comanda` aceita `data: CancelarComandaRequest`, chama `increment_version` → 409 se stale.
- [ ] **D3.** `api/routes/comandas.py`: rota `cancelar_comanda` aceita body `CancelarComandaRequest`.

### Bloco E — Remover TENANT_ID = 1 hardcoded

- [ ] **E1.** `services/users_service.py`: remover `TENANT_ID = 1`, adicionar `tenant_id: int` como parâmetro nas funções que o usam. Atualizar chamadas nos routes.
- [ ] **E2.** `services/profiles_service.py`: mesmo que E1.
- [ ] **E3.** `services/auth_service.py`: remover `TENANT_ID = 1`. Para login, passar `tenant_id=1` no call site até Issue 3 adicionar onboarding.
- [ ] **E4.** `api/routes/users.py` e `api/routes/profiles.py`: extrair `tenant_id` do payload JWT e passar aos services.

### Bloco F — Testes

- [ ] **F1.** `tests/test_issue2_cas.py`: teste `aplicar_desconto` com versão stale → 409; `cancelar_comanda` com versão stale → 409.
- [ ] **F2.** `tests/test_issue2_concorrencia.py`: (PostgreSQL-only) duas threads simultâneas reservando mesmo insumo → estoque final correto sem lost update.

---

## Validações

```bash
cd backend
ruff check src/ tests/
mypy src/
pytest -q
```

---

## Acceptance Criteria

- [ ] get_db executa SET LOCAL app.tenant_id derivado do JWT antes de qualquer query
- [ ] tenant_id nunca lido de header HTTP ou body — apenas do JWT assinado
- [ ] _reservar_estoque usa get_insumo_for_update (SELECT FOR UPDATE)
- [ ] _baixar_insumo usa get_insumo_for_update (SELECT FOR UPDATE)
- [ ] aplicar_desconto passa por increment_version CAS → 409 com versão stale
- [ ] cancelar_comanda passa por increment_version CAS → 409 com versão stale
- [ ] Nenhum TENANT_ID = 1 hardcoded em auth_service, users_service, profiles_service
- [ ] Teste: aplicar_desconto versão stale → 409
- [ ] Teste: cancelar_comanda versão stale → 409
- [ ] Teste: duas threads lançando mesmo insumo → estoque correto (PostgreSQL)

---

## Notas Técnicas

- `get_tenant_db` usa `get_settings().DATABASE_URL.startswith("postgresql")` para guard (SQLite ignora)
- `SET LOCAL app.tenant_id` (não `SET`) — escopo de transação, não vaza entre requests no pool
- `with_for_update()` é ignorado silenciosamente pelo SQLite — sem impacto em testes
- FastAPI faz cache de Depends dentro de um request — `get_current_user` chamado uma só vez mesmo que `get_tenant_db` e `require_permission` dependam dele
- Testes de comandas usam real SQLite + override de `get_current_user` → compatível com `get_tenant_db`
