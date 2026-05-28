import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

import jwt
import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.core.database import Base
from src.services.auth_service import create_access_token

_JWT_SECRET = "test-secret-only-for-tests-32chars!!"
_SQLITE_URL = "sqlite:///:memory:"
_engine = create_engine(_SQLITE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
_Session = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


def test_access_token_contains_subscription_status():
    token = create_access_token({"user_id": 1, "tenant_id": 2, "subscription_status": "ativa"})
    payload = jwt.decode(token, _JWT_SECRET, algorithms=["HS256"])
    assert payload["subscription_status"] == "ativa"


def test_access_token_contains_tenant_id():
    token = create_access_token({"user_id": 1, "tenant_id": 42})
    payload = jwt.decode(token, _JWT_SECRET, algorithms=["HS256"])
    assert payload["tenant_id"] == 42


def test_token_ttl_under_15_minutes(monkeypatch):
    import src.services.auth_service as auth_svc

    class _FakeSettings:
        JWT_SECRET = _JWT_SECRET
        JWT_EXPIRES_MINUTES = 15

    monkeypatch.setattr(auth_svc, "get_settings", lambda: _FakeSettings())

    before = datetime.now(timezone.utc)
    token = create_access_token({"user_id": 1})
    payload = jwt.decode(token, _JWT_SECRET, algorithms=["HS256"])
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    assert (exp - before).total_seconds() <= 15 * 60 + 5


def test_rotate_refresh_token_reloads_subscription_status(monkeypatch):
    import src.services.auth_service as auth_svc
    import src.repositories.refresh_tokens_repository as rt_repo

    class _FakeAssinatura:
        status = "suspensa"

    future = datetime.now(timezone.utc) + timedelta(days=7)

    class _FakeRecord:
        id = 1
        user_id = 10
        revoked_at = None
        expires_at = future.replace(tzinfo=None)

    class _FakeProfile:
        name = "Admin"
        permissions = []

    class _FakeUser:
        id = 10
        tenant_id = 5
        username = "user"
        name = "User"
        profile_id = 1
        profile = _FakeProfile()
        is_active = True

    monkeypatch.setattr(rt_repo, "get_by_hash", lambda db, h: _FakeRecord())
    monkeypatch.setattr(rt_repo, "revoke", lambda db, id: None)
    monkeypatch.setattr(rt_repo, "create", lambda db, uid, h, exp: None)
    monkeypatch.setattr(auth_svc, "get_user_by_id", lambda db, uid: _FakeUser())
    monkeypatch.setattr(auth_svc, "get_assinatura_by_tenant", lambda db, tid: _FakeAssinatura())

    class _FakeSettings:
        JWT_SECRET = _JWT_SECRET
        JWT_EXPIRES_MINUTES = 15
        REFRESH_TOKEN_EXPIRES_DAYS = 7

    monkeypatch.setattr(auth_svc, "get_settings", lambda: _FakeSettings())

    new_access, new_refresh = auth_svc.rotate_refresh_token(None, "raw-token")
    payload = jwt.decode(new_access, _JWT_SECRET, algorithms=["HS256"])
    assert payload["subscription_status"] == "suspensa"


def test_no_default_tenant_id_in_auth_service():
    import src.services.auth_service as auth_svc
    assert not hasattr(auth_svc, "_DEFAULT_TENANT_ID")
