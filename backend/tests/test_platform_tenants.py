import os
from datetime import datetime, timezone

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine, select
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_db
from src.core.database import Base, get_platform_db
from src.main import app
from src.models.assinaturas import Assinatura
from src.models.platform_admin import PlatformAdmin
from src.models.profiles import Profile, ProfilePermission
from src.models.system_users import SystemUser
from src.models.tenants import Tenant
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


def _platform_token() -> str:
    return create_access_token({"platform_admin": True, "admin_id": 1, "email": "admin@platform.com"})


def _tenant_token(tenant_id: int = 1) -> str:
    return create_access_token({"user_id": 1, "tenant_id": tenant_id, "permissions": []})


def _seed_tenants(count: int = 2) -> list[Tenant]:
    db = _Session()
    now = datetime.now(timezone.utc)
    tenants = []
    for i in range(1, count + 1):
        t = Tenant(id=i, nome_fantasia=f"Empresa {i}", cnpj=f"00.000.000/000{i}-00", status="ativo", created_at=now)
        db.add(t)
        tenants.append(t)
    db.commit()
    db.close()
    return tenants


def _seed_assinatura(tenant_id: int, status: str = "trial") -> Assinatura:
    db = _Session()
    now = datetime.now(timezone.utc)
    a = Assinatura(tenant_id=tenant_id, status=status, data_inicio=now, created_at=now, updated_at=now)
    db.add(a)
    db.commit()
    db.close()
    return a


def _seed_user_with_profile(tenant_id: int) -> SystemUser:
    db = _Session()
    now = datetime.now(timezone.utc)
    profile = Profile(tenant_id=tenant_id, name="Admin", created_at=now, updated_at=now)
    db.add(profile)
    db.flush()
    user = SystemUser(
        tenant_id=tenant_id,
        profile_id=profile.id,
        name="Usuário Teste",
        username="usuario_teste",
        password_hash=hash_password("senha123"),
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    db.close()
    return user


# ── D1: GET /platform/tenants retorna lista ──────────────────────────────────

def test_list_tenants_returns_all(client):
    _seed_tenants(2)
    _seed_assinatura(1, "ativa")
    _seed_assinatura(2, "trial")
    resp = client.get("/api/platform/tenants", headers={"Authorization": f"Bearer {_platform_token()}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    ids = {t["id"] for t in data}
    assert ids == {1, 2}


# ── D2: GET /platform/tenants?status= filtra ─────────────────────────────────

def test_list_tenants_filter_by_status(client):
    _seed_tenants(2)
    _seed_assinatura(1, "ativa")
    _seed_assinatura(2, "trial")
    resp = client.get(
        "/api/platform/tenants?status=ativa",
        headers={"Authorization": f"Bearer {_platform_token()}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["status_assinatura"] == "ativa"


# ── D3: GET /platform/tenants/{id}/users ─────────────────────────────────────

def test_get_tenant_users(client):
    _seed_tenants(1)
    _seed_user_with_profile(tenant_id=1)
    resp = client.get(
        "/api/platform/tenants/1/users",
        headers={"Authorization": f"Bearer {_platform_token()}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["username"] == "usuario_teste"
    assert data[0]["profile_name"] == "Admin"


# ── D4: PATCH assinatura atualiza status ─────────────────────────────────────

def test_patch_assinatura_updates_status(client):
    _seed_tenants(1)
    _seed_assinatura(1, "trial")
    resp = client.patch(
        "/api/platform/tenants/1/assinatura",
        json={"status": "ativa"},
        headers={"Authorization": f"Bearer {_platform_token()}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ativa"

    # Confirm via GET
    resp2 = client.get(
        "/api/platform/tenants?status=ativa",
        headers={"Authorization": f"Bearer {_platform_token()}"},
    )
    assert len(resp2.json()) == 1


def test_patch_assinatura_creates_if_not_exists(client):
    _seed_tenants(1)
    resp = client.patch(
        "/api/platform/tenants/1/assinatura",
        json={"status": "suspensa"},
        headers={"Authorization": f"Bearer {_platform_token()}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "suspensa"


# ── D5: token de tenant rejeitado com 403 ────────────────────────────────────

def test_tenant_token_rejected_list(client):
    _seed_tenants(1)
    resp = client.get(
        "/api/platform/tenants",
        headers={"Authorization": f"Bearer {_tenant_token()}"},
    )
    assert resp.status_code == 403


def test_tenant_token_rejected_users(client):
    _seed_tenants(1)
    resp = client.get(
        "/api/platform/tenants/1/users",
        headers={"Authorization": f"Bearer {_tenant_token()}"},
    )
    assert resp.status_code == 403


def test_tenant_token_rejected_patch(client):
    _seed_tenants(1)
    resp = client.patch(
        "/api/platform/tenants/1/assinatura",
        json={"status": "ativa"},
        headers={"Authorization": f"Bearer {_tenant_token()}"},
    )
    assert resp.status_code == 403


# ── D6: sem token → 401 ──────────────────────────────────────────────────────

def test_no_token_returns_401_list(client):
    resp = client.get("/api/platform/tenants")
    assert resp.status_code == 401


def test_no_token_returns_401_users(client):
    resp = client.get("/api/platform/tenants/1/users")
    assert resp.status_code == 401


def test_no_token_returns_401_patch(client):
    resp = client.patch("/api/platform/tenants/1/assinatura", json={"status": "ativa"})
    assert resp.status_code == 401


# ── D7: PATCH /platform/tenants/{id}/profiles/{profile_id} atualiza permissões ──

def test_patch_tenant_profile_updates_permissions(client):
    # tenant_id=2 (not 1) so the assertion below can't be masked by
    # conftest's sqlite patch of tenant_id's server_default to literal 1.
    _seed_tenants(2)
    _seed_user_with_profile(tenant_id=2)
    db = _Session()
    profile_id = db.execute(select(Profile.id).where(Profile.tenant_id == 2)).scalar_one()
    db.close()
    resp = client.patch(
        f"/api/platform/tenants/2/profiles/{profile_id}",
        json={"permissions": ["dashboard", "financeiro"], "is_active": True},
        headers={"Authorization": f"Bearer {_platform_token()}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == profile_id
    assert set(data["permissions"]) == {"dashboard", "financeiro"}

    db = _Session()
    rows = db.execute(
        select(ProfilePermission).where(ProfilePermission.profile_id == profile_id)
    ).scalars().all()
    db.close()
    assert len(rows) == 2
    assert all(r.tenant_id == 2 for r in rows)
    assert all(r.can_access is True for r in rows)
