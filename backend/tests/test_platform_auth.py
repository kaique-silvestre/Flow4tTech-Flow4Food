import os
from datetime import datetime, timezone

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_current_user, get_db
from src.core.database import Base, get_platform_db
from src.main import app
from src.models.platform_admin import PlatformAdmin
from src.services.auth_service import create_access_token, hash_password

_JWT_SECRET = "test-secret-only-for-tests-32chars!!"

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
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
def client():
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_platform_db] = _override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _seed_admin(email: str = "admin@platform.com", password: str = "secret123", is_active: bool = True) -> PlatformAdmin:
    db = _Session()
    admin = PlatformAdmin(
        email=email,
        name="Platform Admin",
        password_hash=hash_password(password),
        is_active=is_active,
        created_at=datetime.now(timezone.utc),
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    db.close()
    return admin


def _make_tenant_token() -> str:
    return create_access_token({
        "sub": "99",
        "user_id": 99,
        "tenant_id": 1,
        "permissions": ["dashboard"],
    })


def _make_platform_token(admin_id: int = 1) -> str:
    return create_access_token({
        "sub": str(admin_id),
        "platform_admin_id": admin_id,
        "platform_admin": True,
        "email": "admin@platform.com",
    })


# G1 — login válido → JWT com platform_admin=True
def test_platform_login_valid(client):
    _seed_admin(email="admin@platform.com", password="secret123")
    resp = client.post("/api/platform/auth/login", json={"email": "admin@platform.com", "password": "secret123"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "access_token" in body
    payload = jwt.decode(body["access_token"], _JWT_SECRET, algorithms=["HS256"])
    assert payload["platform_admin"] is True
    assert "tenant_id" not in payload


# G2 — JWT de tenant rejeitado em rota protegida com 403
def test_tenant_token_rejected_on_platform_route(client):
    tenant_token = _make_tenant_token()
    resp = client.get("/api/platform/auth/login", headers={"Authorization": f"Bearer {tenant_token}"})
    # GET on login is not a valid route, test a protected route instead
    # We add a protected endpoint test via the router's dependency
    # Use a workaround: POST /api/platform/auth/login with tenant token (route is public, won't test dep)
    # Instead verify via dependency directly by checking a route that requires platform admin
    # The router itself has the dependency - any route under protected router
    # Since we only have login (public), test the dependency function directly
    from fastapi import HTTPException
    from fastapi.security import HTTPAuthorizationCredentials
    from src.api.dependencies import require_platform_admin
    import pytest as pt
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=tenant_token)
    with pt.raises(HTTPException) as exc_info:
        require_platform_admin(creds)
    assert exc_info.value.status_code == 403


# G3 — request sem token → 401
def test_no_token_returns_401(client):
    from fastapi import HTTPException
    from src.api.dependencies import require_platform_admin
    import pytest as pt
    with pt.raises(HTTPException) as exc_info:
        require_platform_admin(None)
    assert exc_info.value.status_code == 401


# G4 — senha errada → 401
def test_wrong_password_returns_401(client):
    _seed_admin(email="admin@platform.com", password="correct")
    resp = client.post("/api/platform/auth/login", json={"email": "admin@platform.com", "password": "wrong"})
    assert resp.status_code == 401, resp.text


# G5 — admin inativo → 401
def test_inactive_admin_returns_401(client):
    _seed_admin(email="inactive@platform.com", password="secret123", is_active=False)
    resp = client.post("/api/platform/auth/login", json={"email": "inactive@platform.com", "password": "secret123"})
    assert resp.status_code == 401, resp.text
