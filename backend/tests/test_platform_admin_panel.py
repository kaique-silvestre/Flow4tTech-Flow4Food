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
from src.services import audit_service
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


@pytest.fixture
def audit_calls(monkeypatch):
    """Capture background audit events without writing outside the test session."""
    calls = []

    def _fake_log_background(action, **kwargs):
        calls.append({"action": action, **kwargs})

    monkeypatch.setattr(audit_service, "log_background", _fake_log_background)
    return calls


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


def _seed_default_profiles() -> None:
    """Create the system-profile source tenant used by tenant onboarding."""
    db = _Session()
    now = datetime.now(timezone.utc)
    seed = Tenant(id=1, nome_fantasia="Perfis padrão", status="ativo", created_at=now)
    db.add(seed)
    db.flush()
    for name, screens in (("Admin", ["dashboard", "gestao_usuarios"]), ("Caixa", ["caixa"])):
        profile = Profile(
            tenant_id=seed.id,
            name=name,
            is_system=True,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(profile)
        db.flush()
        for screen in screens:
            db.add(
                ProfilePermission(
                    tenant_id=seed.id,
                    profile_id=profile.id,
                    screen=screen,
                    can_access=True,
                    created_at=now,
                )
            )
    db.commit()
    db.close()


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
    _seed_default_profiles()
    resp = client.post(
        "/api/platform/tenants",
        json={
            "nome_fantasia": "Nova Empresa",
            "max_users": 5,
            "endereco": "Rua das Flores, 10",
            "telefone": "(11) 99999-0000",
            "admin_name": "Ana Admin",
            "admin_username": "ana.admin",
            "admin_email": "ana@novaempresa.com",
            "admin_password": "senha-segura",
        },
        headers=_auth(),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["nome_fantasia"] == "Nova Empresa"
    assert data["status_assinatura"] == "trial"
    assert data["data_vencimento"] is not None


def test_platform_tenant_creation_provisions_profiles_owner_and_login(client):
    """JWT provisioning must have the same usable onboarding as legacy admin."""
    _seed_default_profiles()
    response = client.post(
        "/api/platform/tenants",
        json={
            "nome_fantasia": "Nova Empresa",
            "max_users": 5,
            "endereco": "Rua das Flores, 10",
            "telefone": "(11) 99999-0000",
            "admin_name": "Ana Admin",
            "admin_username": "ana.admin",
            "admin_email": "ana@novaempresa.com",
            "admin_password": "senha-segura",
        },
        headers=_auth(),
    )

    assert response.status_code == 201, response.text
    tenant_id = response.json()["id"]
    assert response.json()["max_users"] == 5
    assert response.json()["qtd_usuarios"] == 1
    detail = client.get(f"/api/platform/tenants/{tenant_id}", headers=_auth())
    assert detail.status_code == 200
    assert detail.json()["endereco"] == "Rua das Flores, 10"
    assert detail.json()["telefone"] == "(11) 99999-0000"
    db = _Session()
    try:
        profiles = db.query(Profile).filter(Profile.tenant_id == tenant_id).all()
        owner = db.query(SystemUser).filter(SystemUser.tenant_id == tenant_id).one()
    finally:
        db.close()
    assert {profile.name for profile in profiles} == {"Admin", "Caixa"}
    assert owner.is_owner is True
    assert owner.profile_id == next(profile.id for profile in profiles if profile.name == "Admin")

    login = client.post(
        "/api/auth/login",
        json={"identifier": "ana.admin", "password": "senha-segura"},
    )
    assert login.status_code == 200, login.text
    assert login.json()["access_token"]


def test_create_tenant_custom_trial_days(client):
    _seed_default_profiles()
    resp = client.post(
        "/api/platform/tenants",
        json={
            "nome_fantasia": "Empresa X",
            "max_users": 10,
            "trial_days": 30,
            "admin_name": "Ana Admin",
            "admin_username": "ana.admin",
            "admin_email": "ana@novaempresa.com",
            "admin_password": "senha-segura",
        },
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


def test_platform_setting_update_is_audited_by_platform_admin(client, audit_calls):
    _seed_setting("trial_duration_days", "14")

    response = client.patch(
        "/api/platform/settings/trial_duration_days", json={"value": "30"}, headers=_auth()
    )

    assert response.status_code == 200
    assert audit_calls == [{
        "action": "platform.setting.update",
        "user_id": 1,
        "entity": "PlatformSettings",
        "entity_id": None,
        "before": {"value": "14"},
        "after": {"key": "trial_duration_days", "value": "30"},
    }]


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


def test_platform_user_creation_is_audited_without_password(client, audit_calls):
    tenant = _seed_tenant()

    response = client.post(
        f"/api/platform/tenants/{tenant.id}/users",
        json={"name": "Novo Usuário", "username": "novo_user", "password": "segredo-nao-auditar"},
        headers=_auth(),
    )

    assert response.status_code == 201
    call = audit_calls.pop()
    assert call["action"] == "platform.tenant_user.create"
    assert call["user_id"] == 1
    assert call["tenant_id"] == tenant.id
    assert call["entity"] == "SystemUser"
    assert call["entity_id"] == response.json()["id"]
    assert call["after"] == {"username": "novo_user", "profile_id": None, "is_active": True}
    assert "segredo-nao-auditar" not in str(call)


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


def test_platform_user_update_audits_password_change_without_password(client, audit_calls):
    tenant = _seed_tenant()
    user = _seed_user(tenant.id)

    response = client.patch(
        f"/api/platform/tenants/{tenant.id}/users/{user.id}",
        json={"name": "Nome Atualizado", "password": "segredo-nao-auditar", "is_active": False},
        headers=_auth(),
    )

    assert response.status_code == 200
    call = audit_calls.pop()
    assert call["action"] == "platform.tenant_user.update"
    assert call["user_id"] == 1
    assert call["tenant_id"] == tenant.id
    assert call["entity"] == "SystemUser"
    assert call["entity_id"] == user.id
    assert call["before"]["is_active"] is True
    assert call["after"]["password_changed"] is True
    assert "segredo-nao-auditar" not in str(call)


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


def test_tenant_features_update_is_audited(client, audit_calls):
    tenant = _seed_tenant()

    response = client.put(
        f"/api/platform/tenants/{tenant.id}/features",
        json={"features": {"compras": True, "relatorios": False}},
        headers=_auth(),
    )

    assert response.status_code == 200
    assert audit_calls == [{
        "action": "platform.tenant_features.update",
        "tenant_id": tenant.id,
        "user_id": 1,
        "entity": "TenantFeature",
        "entity_id": None,
        "before": {},
        "after": {"compras": True, "relatorios": False},
    }]


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


def test_profile_permissions_update_is_audited(client, audit_calls):
    tenant = _seed_tenant()
    profile = _seed_profile(tenant.id, "Caixa")

    response = client.patch(
        f"/api/platform/tenants/{tenant.id}/profiles/{profile.id}",
        json={"permissions": ["dashboard", "caixa"], "is_active": False},
        headers=_auth(),
    )

    assert response.status_code == 200
    assert audit_calls == [{
        "action": "platform.profile.update",
        "tenant_id": tenant.id,
        "user_id": 1,
        "entity": "Profile",
        "entity_id": profile.id,
        "before": {"permissions": [], "is_active": True},
        "after": {"permissions": ["caixa", "dashboard"], "is_active": False},
    }]


def test_platform_announcement_creation_is_audited(client, audit_calls):
    tenant = _seed_tenant()

    response = client.post(
        "/api/platform/announcements",
        json={
            "title": "Manutenção",
            "body": "O sistema ficará indisponível.",
            "target": "specific",
            "tenant_ids": [tenant.id],
        },
        headers=_auth(),
    )

    assert response.status_code == 201
    assert audit_calls == [{
        "action": "platform.announcement.create",
        "tenant_id": tenant.id,
        "user_id": 1,
        "entity": "PlatformAnnouncement",
        "entity_id": response.json()["id"],
        "after": {"title": "Manutenção", "target": "specific", "tenant_ids": [tenant.id], "expires_at": None},
    }]
