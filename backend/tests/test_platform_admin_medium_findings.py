"""Onda 10 — achados MÉDIO/BAIXO do módulo platform_admin (ver auditoria-matchpoint-handoff.md).

Cobre:
1. IntegrityError traduzido (CNPJ duplicado na criação de tenant, email duplicado
   na criação de usuário via platform admin).
3. `_decode_platform_admin_id` loga a exceção engolida em vez de silenciá-la.
4. `profile_id` validado contra `tenant_id` ao criar/atualizar usuário via platform admin.
6. Timing side-channel de enumeração de e-mail no login de platform admin.
"""

import os
from datetime import datetime, timezone

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")
os.environ.setdefault("SUPERADMIN_TOKEN", "superadmin-test-token")

import bcrypt
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
from src.models.tenants import Tenant
from src.services import audit_service, platform_auth_service
from src.services.auth_service import create_access_token, hash_password

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_Session = sessionmaker(bind=_engine, autoflush=False, autocommit=False)

_SUPERADMIN_HEADERS = {
    "Authorization": "Bearer superadmin-test-token",
    "X-Admin-Identifier": "kaique@flow4tech.com",
}


def _seed_profiles(db) -> None:
    existing = db.query(Tenant).filter(Tenant.id == 1).first()
    if existing:
        return
    now = datetime.now(timezone.utc)
    tenant = Tenant(id=1, nome_fantasia="Tenant Padrão", status="ativo", created_at=now)
    db.add(tenant)
    db.flush()
    profile = Profile(
        tenant_id=tenant.id,
        name="Admin",
        description="Acesso total",
        is_system=True,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(profile)
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


def _override_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SUPERADMIN_TOKEN", "superadmin-test-token")
    from src.core import config as cfg_module

    cfg_module.get_settings.cache_clear()
    # BackgroundTasks run inline under TestClient — avoid hitting the real
    # audit_logs table (not the focus of these tests, and not always present
    # in the minimal schema created here).
    monkeypatch.setattr(audit_service, "log_background", lambda *a, **k: None)
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_platform_db] = _override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    cfg_module.get_settings.cache_clear()


def _platform_token() -> str:
    return create_access_token({"platform_admin": True, "sub": "1", "admin_id": 1, "email": "admin@platform.com"})


def _platform_headers() -> dict:
    return {"Authorization": f"Bearer {_platform_token()}"}


# --- Item 1: IntegrityError traduzido ------------------------------------------------


def test_create_tenant_duplicate_cnpj_returns_409_not_500(client):
    payload = {
        "nome_fantasia": "Restaurante A",
        "cnpj": "12.345.678/0001-99",
        "admin_name": "João Silva",
        "admin_username": "joao.silva",
        "admin_email": "joao@restaurante.com",
        "admin_password": "senha123",
    }
    resp1 = client.post("/api/admin/tenants", json=payload, headers=_SUPERADMIN_HEADERS)
    assert resp1.status_code == 201, resp1.text

    payload2 = {**payload, "admin_username": "joao.silva2", "admin_email": "joao2@restaurante.com"}
    resp2 = client.post("/api/admin/tenants", json=payload2, headers=_SUPERADMIN_HEADERS)
    assert resp2.status_code == 409, resp2.text
    body = resp2.json()
    assert body["error"]["code"] == "CONFLICT"


def test_create_platform_user_duplicate_email_returns_409_not_500(client):
    db = _Session()
    now = datetime.now(timezone.utc)
    tenant = Tenant(nome_fantasia="Empresa Teste", status="ativa", max_users=10, created_at=now)
    db.add(tenant)
    db.commit()
    tid = tenant.id
    db.close()

    payload = {"name": "João", "username": "joao", "email": "joao@dup.com", "password": "secret"}
    resp1 = client.post(f"/api/platform/tenants/{tid}/users", json=payload, headers=_platform_headers())
    assert resp1.status_code == 201, resp1.text

    payload2 = {**payload, "username": "joao2"}
    resp2 = client.post(f"/api/platform/tenants/{tid}/users", json=payload2, headers=_platform_headers())
    assert resp2.status_code == 409, resp2.text
    body = resp2.json()
    assert body["error"]["code"] == "CONFLICT"


# --- Item 4: profile_id validado contra tenant_id -------------------------------------


def test_create_platform_user_rejects_profile_from_other_tenant(client):
    db = _Session()
    now = datetime.now(timezone.utc)
    tenant_a = Tenant(nome_fantasia="Tenant A", status="ativa", max_users=10, created_at=now)
    tenant_b = Tenant(nome_fantasia="Tenant B", status="ativa", max_users=10, created_at=now)
    db.add_all([tenant_a, tenant_b])
    db.flush()
    profile_b = Profile(tenant_id=tenant_b.id, name="Admin", is_active=True, created_at=now, updated_at=now)
    db.add(profile_b)
    db.commit()
    tid_a, pid_b = tenant_a.id, profile_b.id
    db.close()

    payload = {"name": "João", "username": "joao", "password": "secret", "profile_id": pid_b}
    resp = client.post(f"/api/platform/tenants/{tid_a}/users", json=payload, headers=_platform_headers())
    assert resp.status_code in (409, 422), resp.text


def test_update_platform_user_rejects_profile_from_other_tenant(client):
    db = _Session()
    now = datetime.now(timezone.utc)
    tenant_a = Tenant(nome_fantasia="Tenant A", status="ativa", max_users=10, created_at=now)
    tenant_b = Tenant(nome_fantasia="Tenant B", status="ativa", max_users=10, created_at=now)
    db.add_all([tenant_a, tenant_b])
    db.flush()
    profile_b = Profile(tenant_id=tenant_b.id, name="Admin", is_active=True, created_at=now, updated_at=now)
    db.add(profile_b)
    db.commit()
    tid_a, pid_b = tenant_a.id, profile_b.id
    db.close()

    create_resp = client.post(
        f"/api/platform/tenants/{tid_a}/users",
        json={"name": "João", "username": "joao", "password": "secret"},
        headers=_platform_headers(),
    )
    assert create_resp.status_code == 201, create_resp.text
    uid = create_resp.json()["id"]

    resp = client.patch(
        f"/api/platform/tenants/{tid_a}/users/{uid}",
        json={"profile_id": pid_b},
        headers=_platform_headers(),
    )
    assert resp.status_code in (409, 422), resp.text


# --- Item 3: _decode_platform_admin_id loga exceção engolida --------------------------


def test_decode_platform_admin_id_logs_on_invalid_token(monkeypatch):
    from src.api.routes import platform_auth as platform_auth_routes

    calls = []
    monkeypatch.setattr(
        platform_auth_routes.logger,
        "warning",
        lambda *a, **k: calls.append((a, k)),
    )
    result = platform_auth_routes._decode_platform_admin_id("not-a-valid-jwt")
    assert result is None
    assert len(calls) == 1


# --- Item 6: timing side-channel de enumeração de e-mail --------------------------


def test_login_runs_bcrypt_even_when_admin_does_not_exist(monkeypatch):
    calls = []
    original_checkpw = bcrypt.checkpw

    def _spy_checkpw(password, hashed):
        calls.append((password, hashed))
        return original_checkpw(password, hashed)

    monkeypatch.setattr(bcrypt, "checkpw", _spy_checkpw)

    db = _Session()
    try:
        from src.core.errors import AppError

        with pytest.raises(AppError):
            platform_auth_service.login(db, "nao-existe@platform.com", "qualquer-senha")
    finally:
        db.close()

    assert len(calls) == 1, "bcrypt.checkpw deve rodar mesmo quando o admin não existe"


def test_login_still_succeeds_for_valid_credentials(monkeypatch):
    db = _Session()
    try:
        admin = PlatformAdmin(
            email="admin@platform.com",
            name="Platform Admin",
            password_hash=hash_password("secret123"),
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(admin)
        db.commit()

        token = platform_auth_service.login(db, "admin@platform.com", "secret123")
        assert token
    finally:
        db.close()
