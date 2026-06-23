# PRP — Issue #10: JWT 15min
**GitHub Issue:** #10 | **Type:** AFK

## Contexto

- `JWT_EXPIRES_MINUTES = 15` já configurado em `config.py` ✓
- `create_access_token` usa `settings.JWT_EXPIRES_MINUTES` ✓
- `rotate_refresh_token` lê `user.profile.permissions` do banco ✓
- Faltam testes específicos: expiração default 15min e refresh recomputa permissões

## Tarefas

- [x] A1. Confirmar JWT_EXPIRES_MINUTES=15 em Settings — já está correto
- [ ] A2. Teste: `create_access_token` com settings default (env de test) emite token com exp ≈ agora+15min
- [ ] A3. Teste: `rotate_refresh_token` reemite token com permissões atualizadas do banco
      (criar profile+user+refresh_token no SQLite, adicionar nova permissão, rotate, checar JWT)

## Implementação

Adicionar em `backend/tests/test_auth.py`:

```python
# A2 — default expiry 15 min
def test_create_access_token_default_expiry_is_15_minutes():
    before = datetime.now(timezone.utc)
    token = create_access_token({"user_id": 1})
    payload = jwt.decode(token, _JWT_SECRET, algorithms=["HS256"])
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    expected = before + timedelta(minutes=15)
    assert abs((exp - expected).total_seconds()) < 5


# A3 — rotate recomputa permissões
def test_rotate_refresh_token_recomputes_permissions(monkeypatch):
    import src.services.auth_service as auth_svc
    monkeypatch.setattr(auth_svc, "get_assinatura_by_tenant", lambda db, tid: None)

    db = _Session()
    try:
        now = datetime.now(timezone.utc)
        profile = Profile(id=1, tenant_id=1, name="Gerente",
                          created_at=now, updated_at=now)
        perm = ProfilePermission(id=1, tenant_id=1, profile_id=1,
                                 screen="vendas", can_access=True, created_at=now)
        user = SystemUser(id=1, tenant_id=1, profile_id=1,
                          name="Test User", username="testuser",
                          password_hash=hash_password("pass"),
                          is_active=True, created_at=now, updated_at=now)
        db.add_all([profile, perm, user])
        db.commit()

        raw_refresh = create_refresh_token(db, user.id)

        # add new permission (simulate DB update)
        new_perm = ProfilePermission(id=2, tenant_id=1, profile_id=1,
                                     screen="cozinha", can_access=True, created_at=now)
        db.add(new_perm)
        db.commit()

        db.expire_all()  # force SQLAlchemy to reload relationships
        new_access, new_raw_refresh = rotate_refresh_token(db, raw_refresh)

        payload = jwt.decode(new_access, _JWT_SECRET, algorithms=["HS256"])
        assert set(payload["permissions"]) == {"vendas", "cozinha"}
        assert new_raw_refresh != raw_refresh
    finally:
        db.close()
```

## Validações

- `cd backend && python -m pytest tests/test_auth.py -v`
- `cd backend && python -m pytest` (suite completa)
