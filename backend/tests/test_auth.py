import os
from datetime import datetime, timedelta, timezone

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_current_user, get_db, require_permission
from src.core.database import Base
from src.repositories import revoked_tokens_repository
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


def _override_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def protected_client():
    _app = FastAPI()

    @_app.get("/protected")
    def _protected(user: dict = Depends(get_current_user)):
        return {"ok": True}

    _app.dependency_overrides[get_db] = _override_db
    return TestClient(_app)


@pytest.fixture
def permission_client():
    _app = FastAPI()

    @_app.get("/guarded")
    def _guarded(user: dict = Depends(require_permission("vendas"))):
        return {"ok": True, "user_id": user["user_id"]}

    _app.dependency_overrides[get_db] = _override_db
    return TestClient(_app)


def _make_token(payload: dict, secret: str = _JWT_SECRET, exp_hours: int = 1) -> str:
    data = {**payload, "exp": datetime.now(timezone.utc) + timedelta(hours=exp_hours)}
    return jwt.encode(data, secret, algorithm="HS256")


# --- Issue 1 tests ---

def test_expired_token_rejected(protected_client):
    expired_payload = {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(hours=1)}
    token = jwt.encode(expired_payload, _JWT_SECRET, algorithm="HS256")
    resp = protected_client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_protected_route_without_token(protected_client):
    resp = protected_client.get("/protected")
    assert resp.status_code == 401


def test_require_permission_no_user_id_returns_403(permission_client):
    token = _make_token({"sub": "legacy", "permissions": ["vendas"]})
    resp = permission_client.get("/guarded", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_require_permission_missing_permission_returns_403(permission_client):
    token = _make_token({"sub": "1", "user_id": 1, "permissions": ["cadastros"]})
    resp = permission_client.get("/guarded", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_require_permission_with_correct_permission_returns_200(permission_client):
    token = _make_token({"sub": "1", "user_id": 1, "permissions": ["vendas", "cadastros"]})
    resp = permission_client.get("/guarded", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["user_id"] == 1


def test_create_access_token_uses_jwt_expires_hours(monkeypatch):
    import src.services.auth_service as auth_svc

    class _FakeSettings:
        JWT_SECRET = _JWT_SECRET
        JWT_EXPIRES_HOURS = 2

    monkeypatch.setattr(auth_svc, "get_settings", lambda: _FakeSettings())

    before = datetime.now(timezone.utc)
    token = create_access_token({"user_id": 1})
    payload = jwt.decode(token, _JWT_SECRET, algorithms=["HS256"])
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    expected = before + timedelta(hours=2)
    assert abs((exp - expected).total_seconds()) < 5


# --- Issue 2 tests ---

def test_is_revoked_returns_false_for_unknown_jti():
    db = _Session()
    try:
        assert revoked_tokens_repository.is_revoked(db, "nonexistent-jti") is False
    finally:
        db.close()


def test_revoke_then_is_revoked_returns_true():
    db = _Session()
    try:
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        revoked_tokens_repository.revoke(db, "test-jti-123", future)
        assert revoked_tokens_repository.is_revoked(db, "test-jti-123") is True
    finally:
        db.close()


def test_delete_expired_removes_expired_keeps_valid():
    db = _Session()
    try:
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        revoked_tokens_repository.revoke(db, "expired-1", past)
        revoked_tokens_repository.revoke(db, "expired-2", past)
        revoked_tokens_repository.revoke(db, "valid-1", future)
        deleted = revoked_tokens_repository.delete_expired(db)
        assert deleted == 2
        assert revoked_tokens_repository.is_revoked(db, "valid-1") is True
        assert revoked_tokens_repository.is_revoked(db, "expired-1") is False
    finally:
        db.close()


def test_revoked_token_rejected_on_protected_route(protected_client):
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    db = _Session()
    try:
        revoked_tokens_repository.revoke(db, "revoked-jti-abc", future)
    finally:
        db.close()

    token = _make_token({"sub": "1", "user_id": 1, "jti": "revoked-jti-abc"})
    resp = protected_client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Token revogado"


def test_valid_token_unaffected_by_other_user_logout(protected_client):
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    db = _Session()
    try:
        revoked_tokens_repository.revoke(db, "other-user-jti", future)
    finally:
        db.close()

    token = _make_token({"sub": "2", "user_id": 2, "jti": "my-unique-jti"})
    resp = protected_client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_create_access_token_includes_jti():
    token = create_access_token({"user_id": 1})
    payload = jwt.decode(token, _JWT_SECRET, algorithms=["HS256"])
    assert "jti" in payload
    assert len(payload["jti"]) == 36  # UUID v4
