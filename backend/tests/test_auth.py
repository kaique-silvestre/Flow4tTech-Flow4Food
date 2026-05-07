import os
from datetime import datetime, timedelta, timezone

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests")
os.environ.setdefault("ENV", "test")

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_current_user, get_db
from src.core.database import Base
from src.main import app

_SQLITE_URL = "sqlite:///:memory:"
_engine = create_engine(
    _SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSession = sessionmaker(bind=_engine, autoflush=False, autocommit=False)

_JWT_SECRET = "test-secret-only-for-tests"


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


@pytest.fixture
def auth_client():
    def override_get_db():
        db = _TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def protected_client():
    _app = FastAPI()

    @_app.get("/protected")
    def _protected(user: dict = Depends(get_current_user)):
        return {"ok": True}

    return TestClient(_app)


def test_first_login_auto_provisions(auth_client):
    """First login provisions hash and returns token."""
    resp = auth_client.post("/api/auth/login", json={"senha": "abc123"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 43200


def test_login_ok_after_provisioning(auth_client):
    """Second login with same password returns valid token."""
    auth_client.post("/api/auth/login", json={"senha": "abc123"})
    resp = auth_client.post("/api/auth/login", json={"senha": "abc123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_wrong_password_returns_401(auth_client):
    """After provisioning, wrong password returns 401 SENHA_INCORRETA."""
    auth_client.post("/api/auth/login", json={"senha": "abc123"})
    resp = auth_client.post("/api/auth/login", json={"senha": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "SENHA_INCORRETA"


def test_expired_token_rejected(protected_client):
    """JWT with past exp is rejected on protected endpoint."""
    expired_payload = {
        "sub": "estabelecimento",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    expired_token = jwt.encode(expired_payload, _JWT_SECRET, algorithm="HS256")
    resp = protected_client.get("/protected", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401


def test_protected_route_without_token(protected_client):
    """Protected endpoint without token returns 401."""
    resp = protected_client.get("/protected")
    assert resp.status_code == 401
