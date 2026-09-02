"""Security hardening tests for the legacy /api/admin superadmin routes."""

import os
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")
os.environ.setdefault("SUPERADMIN_TOKEN", "superadmin-test-token")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_db
from src.api.routes import admin as admin_routes
from src.core.database import Base
from src.core.limiter import limiter
from src.main import app
from src.services import audit_service

_SQLITE_URL = "sqlite:///:memory:"
_engine = create_engine(
    _SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_Session = sessionmaker(bind=_engine, autoflush=False, autocommit=False)

_SUPERADMIN_HEADERS = {
    "Authorization": "Bearer superadmin-test-token",
    "X-Admin-Identifier": "kaique@flow4tech.com",
}

_TENANT_PAYLOAD = {
    "nome_fantasia": "Restaurante Teste",
    "cnpj": "12.345.678/0001-99",
    "admin_name": "João Silva",
    "admin_username": "joao.silva",
    "admin_email": "joao@restaurante.com",
    "admin_password": "senha123",
}


def _seed_profiles(db) -> None:
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

    db.add(
        Assinatura(tenant_id=tenant.id, status="trial", data_inicio=now, created_at=now, updated_at=now)
    )
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
def audit_calls(monkeypatch):
    calls = []

    def _fake_log_background(action, **kwargs):
        calls.append({"action": action, **kwargs})

    monkeypatch.setattr(audit_service, "log_background", _fake_log_background)
    return calls


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SUPERADMIN_TOKEN", "superadmin-test-token")

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


# --- Item 1: constant-time token comparison ---


def test_require_superadmin_uses_constant_time_compare(client):
    with patch(
        "src.api.routes.admin.hmac.compare_digest", wraps=admin_routes.hmac.compare_digest
    ) as spy:
        r = client.post("/api/admin/tenants", json=_TENANT_PAYLOAD, headers=_SUPERADMIN_HEADERS)
        assert r.status_code == 201, r.text
        assert spy.called


def test_require_superadmin_rejects_wrong_token_via_compare_digest(client):
    with patch(
        "src.api.routes.admin.hmac.compare_digest", wraps=admin_routes.hmac.compare_digest
    ) as spy:
        r = client.post(
            "/api/admin/tenants",
            json=_TENANT_PAYLOAD,
            headers={**_SUPERADMIN_HEADERS, "Authorization": "Bearer wrong-token"},
        )
        assert r.status_code == 403
        assert spy.called


# --- Item 2 & 3: audit logging with admin identifier ---


def test_create_tenant_is_audited_with_admin_identifier(client, audit_calls):
    r = client.post("/api/admin/tenants", json=_TENANT_PAYLOAD, headers=_SUPERADMIN_HEADERS)
    assert r.status_code == 201, r.text
    assert len(audit_calls) == 1
    assert audit_calls[0]["action"] == "admin.tenant_create"
    assert audit_calls[0]["after"]["admin_identifier"] == "kaique@flow4tech.com"


def test_update_tenant_is_audited_with_admin_identifier(client, audit_calls):
    create_r = client.post("/api/admin/tenants", json=_TENANT_PAYLOAD, headers=_SUPERADMIN_HEADERS)
    tenant_id = create_r.json()["id"]
    audit_calls.clear()

    r = client.patch(
        f"/api/admin/tenants/{tenant_id}",
        json={"nome_fantasia": "Novo Nome"},
        headers=_SUPERADMIN_HEADERS,
    )
    assert r.status_code == 200
    assert len(audit_calls) == 1
    assert audit_calls[0]["action"] == "admin.tenant_update"
    assert audit_calls[0]["after"]["admin_identifier"] == "kaique@flow4tech.com"


def test_mutation_without_admin_identifier_header_is_rejected(client, audit_calls):
    headers = {"Authorization": "Bearer superadmin-test-token"}
    r = client.post("/api/admin/tenants", json=_TENANT_PAYLOAD, headers=headers)
    assert r.status_code == 400
    assert audit_calls == []


def test_mutation_with_blank_admin_identifier_header_is_rejected(client, audit_calls):
    headers = {"Authorization": "Bearer superadmin-test-token", "X-Admin-Identifier": "   "}
    r = client.post("/api/admin/tenants", json=_TENANT_PAYLOAD, headers=headers)
    assert r.status_code == 400
    assert audit_calls == []


def test_read_only_route_does_not_require_admin_identifier(client, audit_calls):
    headers = {"Authorization": "Bearer superadmin-test-token"}
    r = client.get("/api/admin/tenants", headers=headers)
    assert r.status_code == 200
    assert audit_calls == []


# --- Item 4: rate limiting ---


def test_admin_routes_rate_limited_after_repeated_attempts(client, monkeypatch):
    monkeypatch.setattr(limiter, "enabled", True)
    limiter.reset()

    statuses = [
        client.get("/api/admin/tenants", headers=_SUPERADMIN_HEADERS).status_code for _ in range(5)
    ]
    limiter.reset()
    assert 429 in statuses


def test_admin_routes_rate_limit_counts_wrong_token_attempts(client, monkeypatch):
    """A wrong-token request must still consume a rate-limit slot.

    Otherwise an attacker could brute-force SUPERADMIN_TOKEN forever, since
    every guess would be rejected with 403 *before* ever being counted.
    """
    monkeypatch.setattr(limiter, "enabled", True)
    limiter.reset()
    wrong_headers = {"Authorization": "Bearer wrong-token"}

    statuses = [
        client.get("/api/admin/tenants", headers=wrong_headers).status_code for _ in range(5)
    ]
    limiter.reset()
    assert all(s == 403 for s in statuses[:3])
    assert 429 in statuses[3:]
