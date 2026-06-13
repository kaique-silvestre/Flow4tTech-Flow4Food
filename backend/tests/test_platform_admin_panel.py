"""Tests for issue #25 — Platform Admin Panel new endpoints."""
import os
from datetime import datetime, timedelta, timezone

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_db
from src.core.database import Base, get_platform_db
from src.main import app
from src.models.assinaturas import Assinatura
from src.models.platform_admin import PlatformAdmin
from src.models.platform_announcements import PlatformAnnouncement
from src.models.platform_settings import PlatformSettings
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
    return create_access_token({"platform_admin": True, "sub": "1", "admin_id": 1, "email": "admin@platform.com"})


def _tenant_token(tenant_id: int = 1, status: str = "ativa", permissions: list = None) -> str:
    return create_access_token({
        "sub": "1",
        "user_id": 1,
        "tenant_id": tenant_id,
        "permissions": permissions or ["dashboard"],
        "subscription_status": status,
    })


def _seed_tenant(status: str = "ativo") -> Tenant:
    db = _Session()
    now = datetime.now(timezone.utc)
    t = Tenant(nome_fantasia="Empresa Teste", cnpj="00.000.000/0001-00", status=status, max_users=5, created_at=now)
    db.add(t)
    db.commit()
    db.refresh(t)
    db.close()
    return t


def _seed_assinatura(tenant_id: int, status: str = "ativa", days_until_expire: int = None) -> Assinatura:
    db = _Session()
    now = datetime.now(timezone.utc)
    dv = (now + timedelta(days=days_until_expire)) if days_until_expire is not None else None
    a = Assinatura(tenant_id=tenant_id, status=status, data_inicio=now, data_vencimento=dv, created_at=now, updated_at=now)
    db.add(a)
    db.commit()
    db.refresh(a)
    db.close()
    return a


def _seed_setting(key: str, value: str) -> None:
    db = _Session()
    db.add(PlatformSettings(key=key, value=value, updated_at=datetime.now(timezone.utc)))
    db.commit()
    db.close()


def _seed_profile(tenant_id: int, name: str = "Admin") -> Profile:
    db = _Session()
    now = datetime.now(timezone.utc)
    p = Profile(tenant_id=tenant_id, name=name, created_at=now, updated_at=now)
    db.add(p)
    db.commit()
    db.refresh(p)
    db.close()
    return p


def _seed_user(tenant_id: int, profile_id: int = None) -> SystemUser:
    db = _Session()
    now = datetime.now(timezone.utc)
    u = SystemUser(
        tenant_id=tenant_id,
        name="Usuário Teste",
        username="usuario_teste",
        email="user@teste.com",
        password_hash=hash_password("senha123"),
        profile_id=profile_id,
        created_at=now,
        updated_at=now,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    db.close()
    return u


_auth = lambda: {"Authorization": f"Bearer {_platform_token()}"}


# ─── Tenant create ────────────────────────────────────────────────────────────

def test_create_tenant_with_trial(client):
    _seed_setting("trial_duration_days", "14")
    resp = client.post(
        "/api/platform/tenants",
        json={"nome_fantasia": "Nova Empresa", "max_users": 5},
        headers=_auth(),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["nome_fantasia"] == "Nova Empresa"
    assert data["status_assinatura"] == "trial"
    assert data["data_vencimento"] is not None


def test_create_tenant_custom_trial_days(client):
    resp = client.post(
        "/api/platform/tenants",
        json={"nome_fantasia": "Empresa X", "max_users": 10, "trial_days": 30},
        headers=_auth(),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status_assinatura"] == "trial"


# ─── Settings CRUD ───────────────────────────────────────────────────────────

def test_list_settings(client):
    _seed_setting("trial_duration_days", "14")
    resp = client.get("/api/platform/settings", headers=_auth())
    assert resp.status_code == 200
    keys = [s["key"] for s in resp.json()]
    assert "trial_duration_days" in keys


def test_update_setting(client):
    _seed_setting("trial_duration_days", "14")
    resp = client.patch("/api/platform/settings/trial_duration_days", json={"value": "30"}, headers=_auth())
    assert resp.status_code == 200
    assert resp.json()["value"] == "30"


# ─── Subscription blocking ────────────────────────────────────────────────────

def test_suspended_tenant_gets_402(client):
    t = _seed_tenant()
    _seed_assinatura(t.id, status="suspensa")
    token = create_access_token({"sub": "1", "user_id": 1, "tenant_id": t.id, "permissions": ["dashboard"]})
    resp = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 402
    assert "SUBSCRIPTION_BLOCKED" in resp.text


def test_expired_trial_gets_402(client):
    t = _seed_tenant()
    _seed_assinatura(t.id, status="trial", days_until_expire=-1)
    token = create_access_token({"sub": "1", "user_id": 1, "tenant_id": t.id, "permissions": ["dashboard"]})
    resp = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 402


def test_active_tenant_passes_subscription_check(client):
    t = _seed_tenant()
    _seed_assinatura(t.id, status="ativa")
    token = create_access_token({"sub": "1", "user_id": 1, "tenant_id": t.id, "permissions": ["dashboard"]})
    resp = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code in (200, 204, 404)


# ─── Platform user CRUD ───────────────────────────────────────────────────────

def test_create_platform_user(client):
    t = _seed_tenant()
    resp = client.post(
        f"/api/platform/tenants/{t.id}/users",
        json={"name": "Novo Usuário", "username": "novo_user", "password": "senha123"},
        headers=_auth(),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "novo_user"
    assert data["is_active"] is True


def test_update_platform_user(client):
    t = _seed_tenant()
    u = _seed_user(t.id)
    resp = client.patch(
        f"/api/platform/tenants/{t.id}/users/{u.id}",
        json={"name": "Nome Atualizado", "is_active": False},
        headers=_auth(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Nome Atualizado"
    assert data["is_active"] is False


# ─── Feature flags ────────────────────────────────────────────────────────────

def test_get_tenant_features_empty(client):
    t = _seed_tenant()
    resp = client.get(f"/api/platform/tenants/{t.id}/features", headers=_auth())
    assert resp.status_code == 200
    assert resp.json() == []


def test_upsert_tenant_features(client):
    t = _seed_tenant()
    resp = client.put(
        f"/api/platform/tenants/{t.id}/features",
        json={"features": {"compras": True, "relatorios": False}},
        headers=_auth(),
    )
    assert resp.status_code == 200
    features = {f["feature"]: f["enabled"] for f in resp.json()}
    assert features["compras"] is True
    assert features["relatorios"] is False


# ─── Impersonation ────────────────────────────────────────────────────────────

def test_impersonate_user_returns_token(client):
    t = _seed_tenant()
    p = _seed_profile(t.id)
    u = _seed_user(t.id, profile_id=p.id)
    resp = client.post(
        f"/api/platform/tenants/{t.id}/users/{u.id}/impersonate",
        headers=_auth(),
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    payload = jwt.decode(token, _JWT_SECRET, algorithms=["HS256"])
    assert payload["user_id"] == u.id
    assert payload["tenant_id"] == t.id
    assert payload["impersonation"] is True
    assert payload["impersonated_by"] is not None


# ─── Assinatura history ───────────────────────────────────────────────────────

def test_assinatura_history_recorded(client):
    t = _seed_tenant()
    _seed_assinatura(t.id, status="trial")
    client.patch(
        f"/api/platform/tenants/{t.id}/assinatura",
        json={"status": "ativa"},
        headers=_auth(),
    )
    resp = client.get(f"/api/platform/tenants/{t.id}/assinatura/historico", headers=_auth())
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) >= 1
    assert history[0]["to_status"] == "ativa"
    assert history[0]["from_status"] == "trial"


# ─── Tenant detail and update ─────────────────────────────────────────────────

def test_get_tenant_detail(client):
    t = _seed_tenant()
    _seed_assinatura(t.id, "ativa")
    resp = client.get(f"/api/platform/tenants/{t.id}", headers=_auth())
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == t.id
    assert data["nome_fantasia"] == "Empresa Teste"
    assert data["status_assinatura"] == "ativa"


def test_update_tenant(client):
    t = _seed_tenant()
    _seed_assinatura(t.id, "ativa")
    resp = client.patch(
        f"/api/platform/tenants/{t.id}",
        json={"nome_fantasia": "Empresa Atualizada", "max_users": 20},
        headers=_auth(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["nome_fantasia"] == "Empresa Atualizada"
    assert data["max_users"] == 20


# ─── Profiles ────────────────────────────────────────────────────────────────

def test_get_tenant_profiles(client):
    t = _seed_tenant()
    _seed_profile(t.id, "Gerente")
    resp = client.get(f"/api/platform/tenants/{t.id}/profiles", headers=_auth())
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Gerente"


def test_update_profile_permissions(client):
    t = _seed_tenant()
    p = _seed_profile(t.id, "Caixa")
    resp = client.patch(
        f"/api/platform/tenants/{t.id}/profiles/{p.id}",
        json={"permissions": ["dashboard", "caixa"]},
        headers=_auth(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert set(data["permissions"]) == {"dashboard", "caixa"}
