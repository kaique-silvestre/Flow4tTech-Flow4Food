"""Tests for issue #32 — tenant users tab (list, create, update)."""
import os
from datetime import datetime, timezone

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_db
from src.core.database import Base, get_platform_db
from src.main import app
from src.models.assinaturas import Assinatura
from src.models.platform_admin import PlatformAdmin
from src.models.profiles import Profile
from src.models.system_users import SystemUser
from src.models.tenants import Tenant
from src.services.auth_service import create_access_token, hash_password

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


def _platform_token() -> str:
    return create_access_token({"platform_admin": True, "sub": "1", "admin_id": 1, "email": "admin@platform.com"})


def _headers() -> dict:
    return {"Authorization": f"Bearer {_platform_token()}"}


@pytest.fixture
def tenant_with_profile(client: TestClient):
    db = _Session()
    now = datetime.now(timezone.utc)
    admin = PlatformAdmin(email="admin@platform.com", password_hash=hash_password("pw"), name="Admin", created_at=now)
    db.add(admin)
    tenant = Tenant(nome_fantasia="Empresa Teste", status="ativa", max_users=10, created_at=now)
    db.add(tenant)
    db.flush()
    assinatura = Assinatura(tenant_id=tenant.id, status="ativa", data_inicio=now, created_at=now, updated_at=now)
    db.add(assinatura)
    profile = Profile(tenant_id=tenant.id, name="Admin", is_active=True, created_at=now, updated_at=now)
    db.add(profile)
    db.commit()
    tid = tenant.id
    pid = profile.id
    db.close()
    return {"tenant_id": tid, "profile_id": pid}


def test_list_users_empty(client, tenant_with_profile):
    tid = tenant_with_profile["tenant_id"]
    resp = client.get(f"/api/platform/tenants/{tid}/users", headers=_headers())
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_user_returns_full_fields(client, tenant_with_profile):
    tid = tenant_with_profile["tenant_id"]
    pid = tenant_with_profile["profile_id"]
    resp = client.post(
        f"/api/platform/tenants/{tid}/users",
        json={"name": "João", "username": "joao", "email": "joao@test.com", "password": "secret", "profile_id": pid, "is_active": True},
        headers=_headers(),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "João"
    assert body["username"] == "joao"
    assert body["email"] == "joao@test.com"
    assert body["profile_id"] == pid
    assert body["profile_name"] == "Admin"
    assert body["is_active"] is True
    assert body["last_login"] is None


def test_create_user_no_profile(client, tenant_with_profile):
    tid = tenant_with_profile["tenant_id"]
    resp = client.post(
        f"/api/platform/tenants/{tid}/users",
        json={"name": "Maria", "username": "maria", "password": "secret"},
        headers=_headers(),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] is None
    assert body["profile_id"] is None
    assert body["profile_name"] is None


def test_list_users_includes_email_and_profile(client, tenant_with_profile):
    tid = tenant_with_profile["tenant_id"]
    pid = tenant_with_profile["profile_id"]
    client.post(
        f"/api/platform/tenants/{tid}/users",
        json={"name": "Ana", "username": "ana", "email": "ana@x.com", "password": "pw", "profile_id": pid},
        headers=_headers(),
    )
    # User without profile
    client.post(
        f"/api/platform/tenants/{tid}/users",
        json={"name": "Bob", "username": "bob", "password": "pw"},
        headers=_headers(),
    )
    resp = client.get(f"/api/platform/tenants/{tid}/users", headers=_headers())
    assert resp.status_code == 200
    users = resp.json()
    assert len(users) == 2
    ana = next(u for u in users if u["username"] == "ana")
    bob = next(u for u in users if u["username"] == "bob")
    assert ana["email"] == "ana@x.com"
    assert ana["profile_id"] == pid
    assert ana["profile_name"] == "Admin"
    # Bob has no profile — must still appear (outerjoin)
    assert bob["profile_id"] is None
    assert bob["profile_name"] is None


def test_update_user_full_fields(client, tenant_with_profile):
    tid = tenant_with_profile["tenant_id"]
    pid = tenant_with_profile["profile_id"]
    create_resp = client.post(
        f"/api/platform/tenants/{tid}/users",
        json={"name": "Old Name", "username": "olduser", "password": "pw"},
        headers=_headers(),
    )
    uid = create_resp.json()["id"]
    resp = client.patch(
        f"/api/platform/tenants/{tid}/users/{uid}",
        json={"name": "New Name", "username": "newuser", "email": "new@x.com", "profile_id": pid, "is_active": False},
        headers=_headers(),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "New Name"
    assert body["username"] == "newuser"
    assert body["email"] == "new@x.com"
    assert body["profile_id"] == pid
    assert body["is_active"] is False


def test_update_user_password_only_when_sent(client, tenant_with_profile):
    tid = tenant_with_profile["tenant_id"]
    create_resp = client.post(
        f"/api/platform/tenants/{tid}/users",
        json={"name": "User", "username": "user1", "password": "original"},
        headers=_headers(),
    )
    uid = create_resp.json()["id"]
    # Update without password — should not error
    resp = client.patch(
        f"/api/platform/tenants/{tid}/users/{uid}",
        json={"name": "User Updated"},
        headers=_headers(),
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "User Updated"


def test_update_user_not_found(client, tenant_with_profile):
    tid = tenant_with_profile["tenant_id"]
    resp = client.patch(
        f"/api/platform/tenants/{tid}/users/99999",
        json={"name": "X"},
        headers=_headers(),
    )
    assert resp.status_code == 404


def test_toggle_active(client, tenant_with_profile):
    tid = tenant_with_profile["tenant_id"]
    create_resp = client.post(
        f"/api/platform/tenants/{tid}/users",
        json={"name": "User", "username": "u2", "password": "pw", "is_active": True},
        headers=_headers(),
    )
    uid = create_resp.json()["id"]
    resp = client.patch(
        f"/api/platform/tenants/{tid}/users/{uid}",
        json={"is_active": False},
        headers=_headers(),
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False
