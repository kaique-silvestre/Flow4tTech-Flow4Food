"""Issue 3 — Atomic tenant onboarding tests."""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")
os.environ.setdefault("SUPERADMIN_TOKEN", "superadmin-test-token")

import pytest
from fastapi.testclient import TestClient
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
_Session = sessionmaker(bind=_engine, autoflush=False, autocommit=False)

_SUPERADMIN_HEADERS = {"Authorization": "Bearer superadmin-test-token"}
_WRONG_TOKEN_HEADERS = {"Authorization": "Bearer wrong-token"}

_TENANT_PAYLOAD = {
    "nome_fantasia": "Restaurante Teste",
    "cnpj": "12.345.678/0001-99",
    "admin_name": "João Silva",
    "admin_username": "joao.silva",
    "admin_email": "joao@restaurante.com",
    "admin_password": "senha123",
}


def _seed_profiles(db) -> None:
    """Seed tenant_id=1 with default profiles so clone logic has source data.

    Passes created_at/updated_at explicitly to avoid NOW() server_default on SQLite.
    """
    from datetime import datetime, timezone

    from src.models.assinaturas import Assinatura
    from src.models.profiles import Profile, ProfilePermission
    from src.models.tenants import Tenant

    existing = db.query(Tenant).filter(Tenant.id == 1).first()
    if existing:
        return

    now = datetime.now(timezone.utc)

    tenant = Tenant(id=1, nome_fantasia="Tenant Padrão", status="ativo", created_at=now)
    db.add(tenant)
    db.flush()

    for name, desc, screens in [
        ("Admin", "Acesso total", ["dashboard", "gestao_usuarios"]),
        ("Gerente", "Acesso gerencial", ["dashboard"]),
        ("Caixa", "Acesso operacional", ["dashboard", "caixa"]),
    ]:
        p = Profile(
            tenant_id=tenant.id,
            name=name,
            description=desc,
            is_system=True,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(p)
        db.flush()
        for screen in screens:
            db.add(
                ProfilePermission(
                    profile_id=p.id,
                    tenant_id=tenant.id,
                    screen=screen,
                    can_access=True,
                    created_at=now,
                )
            )

    db.add(Assinatura(tenant_id=tenant.id, status="trial", data_inicio=now, created_at=now, updated_at=now))
    db.commit()


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(_engine)
    db = _Session()
    _seed_profiles(db)
    db.close()
    yield
    Base.metadata.drop_all(_engine)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SUPERADMIN_TOKEN", "superadmin-test-token")

    # Clear settings cache so monkeypatch takes effect
    from src.core import config as cfg_module
    cfg_module.get_settings.cache_clear()

    def override_db():
        db = _Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    cfg_module.get_settings.cache_clear()


# --- Auth guard tests ---

def test_post_admin_tenants_requires_superadmin(client):
    r = client.post("/api/admin/tenants", json=_TENANT_PAYLOAD)
    assert r.status_code == 403


def test_post_admin_tenants_wrong_token_returns_403(client):
    r = client.post("/api/admin/tenants", json=_TENANT_PAYLOAD, headers=_WRONG_TOKEN_HEADERS)
    assert r.status_code == 403


def test_get_admin_tenant_requires_superadmin(client):
    r = client.get("/api/admin/tenants/999")
    assert r.status_code == 403


def test_patch_admin_tenant_requires_superadmin(client):
    r = client.patch("/api/admin/tenants/999", json={"nome_fantasia": "X"})
    assert r.status_code == 403


# --- Creation tests ---

def test_post_admin_tenants_creates_tenant(client):
    r = client.post("/api/admin/tenants", json=_TENANT_PAYLOAD, headers=_SUPERADMIN_HEADERS)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["nome_fantasia"] == "Restaurante Teste"
    assert data["status"] == "ativo"
    assert data["admin_user_id"] is not None
    assert data["assinatura"]["status"] == "trial"


def test_created_tenant_has_admin_user_id(client):
    r = client.post("/api/admin/tenants", json=_TENANT_PAYLOAD, headers=_SUPERADMIN_HEADERS)
    assert r.status_code == 201
    assert r.json()["admin_user_id"] is not None


def test_assinatura_is_trial_on_creation(client):
    r = client.post("/api/admin/tenants", json=_TENANT_PAYLOAD, headers=_SUPERADMIN_HEADERS)
    assert r.status_code == 201
    assert r.json()["assinatura"]["status"] == "trial"


def test_post_admin_tenants_conflict_on_duplicate_email(client):
    client.post("/api/admin/tenants", json=_TENANT_PAYLOAD, headers=_SUPERADMIN_HEADERS)
    payload2 = {**_TENANT_PAYLOAD, "nome_fantasia": "Outro Rest", "admin_username": "outro.user"}
    r = client.post("/api/admin/tenants", json=payload2, headers=_SUPERADMIN_HEADERS)
    assert r.status_code == 409, r.text


def test_atomic_rollback_duplicate_email_no_orphan(client):
    """Duplicate email => rollback: second tenant must NOT exist."""
    client.post("/api/admin/tenants", json=_TENANT_PAYLOAD, headers=_SUPERADMIN_HEADERS)

    payload2 = {**_TENANT_PAYLOAD, "nome_fantasia": "Fantasma", "admin_username": "fantasma"}
    r = client.post("/api/admin/tenants", json=payload2, headers=_SUPERADMIN_HEADERS)
    assert r.status_code == 409

    # List tenants — should have only 1 (the seed tenant, id=1)
    # The new failed tenant must not appear
    tenants_r = client.get("/api/admin/tenants", headers=_SUPERADMIN_HEADERS)
    assert tenants_r.status_code == 200
    names = [t["nome_fantasia"] for t in tenants_r.json()]
    assert "Fantasma" not in names


# --- GET / PATCH tests ---

def test_get_admin_tenant_returns_data(client):
    create_r = client.post("/api/admin/tenants", json=_TENANT_PAYLOAD, headers=_SUPERADMIN_HEADERS)
    tenant_id = create_r.json()["id"]

    r = client.get(f"/api/admin/tenants/{tenant_id}", headers=_SUPERADMIN_HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == tenant_id
    assert data["assinatura"]["status"] == "trial"


def test_get_admin_tenant_not_found(client):
    r = client.get("/api/admin/tenants/99999", headers=_SUPERADMIN_HEADERS)
    assert r.status_code == 404


def test_patch_admin_tenant_updates_nome_fantasia(client):
    create_r = client.post("/api/admin/tenants", json=_TENANT_PAYLOAD, headers=_SUPERADMIN_HEADERS)
    tenant_id = create_r.json()["id"]

    r = client.patch(
        f"/api/admin/tenants/{tenant_id}",
        json={"nome_fantasia": "Novo Nome"},
        headers=_SUPERADMIN_HEADERS,
    )
    assert r.status_code == 200
    assert r.json()["nome_fantasia"] == "Novo Nome"


def test_patch_admin_tenant_updates_status(client):
    create_r = client.post("/api/admin/tenants", json=_TENANT_PAYLOAD, headers=_SUPERADMIN_HEADERS)
    tenant_id = create_r.json()["id"]

    r = client.patch(
        f"/api/admin/tenants/{tenant_id}",
        json={"status": "suspensa"},
        headers=_SUPERADMIN_HEADERS,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "suspensa"


def test_patch_admin_tenant_not_found(client):
    r = client.patch(
        "/api/admin/tenants/99999",
        json={"nome_fantasia": "X"},
        headers=_SUPERADMIN_HEADERS,
    )
    assert r.status_code == 404
