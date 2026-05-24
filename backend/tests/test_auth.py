import os
from datetime import datetime, timedelta, timezone

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies import get_current_user, get_db, require_permission
from src.services.auth_service import create_access_token

_JWT_SECRET = "test-secret-only-for-tests-32chars!!"


@pytest.fixture
def protected_client():
    _app = FastAPI()

    @_app.get("/protected")
    def _protected(user: dict = Depends(get_current_user)):
        return {"ok": True}

    return TestClient(_app)


@pytest.fixture
def permission_client():
    _app = FastAPI()

    @_app.get("/guarded")
    def _guarded(user: dict = Depends(require_permission("vendas"))):
        return {"ok": True, "user_id": user["user_id"]}

    return TestClient(_app)


def _make_token(payload: dict, secret: str = _JWT_SECRET, exp_hours: int = 1) -> str:
    data = {**payload, "exp": datetime.now(timezone.utc) + timedelta(hours=exp_hours)}
    return jwt.encode(data, secret, algorithm="HS256")


def test_expired_token_rejected(protected_client):
    expired_payload = {
        "sub": "1",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
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
