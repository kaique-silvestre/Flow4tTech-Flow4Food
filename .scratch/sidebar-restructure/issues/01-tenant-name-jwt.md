# 01: Backend — `tenant_name` no JWT (login e refresh)

**What to build:** Login e refresh de token passam a incluir o nome do tenant (`nome_fantasia`) no payload do JWT, junto dos campos já existentes (`tenant_id`, `subscription_status` etc.), pra que o frontend consiga exibir o nome da empresa sem uma chamada de rede extra.

**Blocked by:** None (can start immediately)

**Touches:** `backend/src/services/auth_service.py`, `backend/tests/test_auth.py`

**Nature:** objective

- [ ] `_build_token_response()` (fluxo de login) inclui `tenant_name` no payload, buscando via `tenant_repository.get_tenant_by_id(db, user.tenant_id)`.
- [ ] `rotate_refresh_token()` (fluxo de refresh) inclui `tenant_name` no novo access token, mesma fonte.
- [ ] Campo é aditivo — nenhum campo existente do payload muda de nome/tipo/valor.
- [ ] `test_auth.py`: teste de login decodifica o JWT e verifica `tenant_name` correto.
- [ ] `test_auth.py`: teste de refresh decodifica o novo access token e verifica `tenant_name` correto.
