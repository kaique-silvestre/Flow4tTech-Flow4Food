"""Tests for issue #36 — audit log global."""
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
from src.models.audit_logs import AuditLog
from src.models.platform_admin import PlatformAdmin
from src.models.system_users import SystemUser
from src.models.tenants import Tenant
from src.services import audit_service
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


def _log_bg_test(action, *, tenant_id=None, user_id=None, entity=None, entity_id=None, before=None, after=None, impersonated_by=None):
    db = _Session()
    try:
        audit_service.log(db, action, tenant_id=tenant_id, user_id=user_id, entity=entity, entity_id=entity_id, before=before, after=after, impersonated_by=impersonated_by)
    finally:
        db.close()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(audit_service, "log_background", _log_bg_test)
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_platform_db] = _override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _platform_token(admin_id: int = 1) -> dict:
    token = create_access_token({"platform_admin": True, "sub": str(admin_id), "admin_id": admin_id, "email": "admin@platform.com"})
    return {"Authorization": f"Bearer {token}"}


def _impersonation_token(user_id: int, tenant_id: int, admin_id: int = 1) -> dict:
    token = create_access_token({
        "sub": str(user_id),
        "user_id": user_id,
        "tenant_id": tenant_id,
        "permissions": ["gestao_usuarios"],
        "subscription_status": "ativa",
        "impersonation": True,
        "impersonated_by": admin_id,
        "impersonated_by_email": "admin@platform.com",
    })
    return {"Authorization": f"Bearer {token}"}


def _seed_base():
    db = _Session()
    now = datetime.now(timezone.utc)
    admin = PlatformAdmin(email="admin@platform.com", password_hash=hash_password("pw"), name="Admin", created_at=now)
    db.add(admin)
    tenant = Tenant(nome_fantasia="Empresa Teste", status="ativa", max_users=10, created_at=now)
    db.add(tenant)
    db.flush()
    assinatura = Assinatura(tenant_id=tenant.id, status="ativa", data_inicio=now, created_at=now, updated_at=now)
    db.add(assinatura)
    owner = SystemUser(
        tenant_id=tenant.id,
        name="Owner",
        username="owner",
        email="owner@test.com",
        password_hash=hash_password("pw"),
        is_active=True,
        is_owner=True,
        created_at=now,
        updated_at=now,
    )
    db.add(owner)
    db.commit()
    tid = tenant.id
    uid = owner.id
    db.close()
    return {"tenant_id": tid, "owner_id": uid}


def test_audit_log_created_on_user_create_during_impersonation(client):
    base = _seed_base()
    tenant_id = base["tenant_id"]
    owner_id = base["owner_id"]

    headers = _impersonation_token(owner_id, tenant_id, admin_id=1)
    resp = client.post(
        "/api/users",
        json={"name": "Novo User", "username": "novousr", "email": "novo@x.com", "password": "pw123456"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text

    db = _Session()
    logs = db.query(AuditLog).filter_by(action="user.create").all()
    db.close()

    assert len(logs) == 1
    log = logs[0]
    assert log.tenant_id == tenant_id
    assert log.impersonated_by == 1
    assert log.entity == "SystemUser"


def test_audit_logs_endpoint_returns_entries(client):
    db = _Session()
    now = datetime.now(timezone.utc)
    tenant = Tenant(nome_fantasia="Tenant A", status="ativa", max_users=5, created_at=now)
    db.add(tenant)
    db.flush()
    db.add(AuditLog(tenant_id=tenant.id, action="user.create", entity="SystemUser", entity_id=10, created_at=now))
    db.add(AuditLog(tenant_id=tenant.id, action="user.delete", entity="SystemUser", entity_id=11, created_at=now))
    db.commit()
    db.close()

    resp = client.get("/api/platform/audit-logs", headers=_platform_token())
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


def test_audit_logs_filter_by_action(client):
    db = _Session()
    now = datetime.now(timezone.utc)
    tenant = Tenant(nome_fantasia="Tenant B", status="ativa", max_users=5, created_at=now)
    db.add(tenant)
    db.flush()
    db.add(AuditLog(tenant_id=tenant.id, action="user.create", created_at=now))
    db.add(AuditLog(tenant_id=tenant.id, action="user.delete", created_at=now))
    db.commit()
    db.close()

    resp = client.get("/api/platform/audit-logs?action=user.create", headers=_platform_token())
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["action"] == "user.create"


def test_audit_logs_filter_by_tenant_id(client):
    db = _Session()
    now = datetime.now(timezone.utc)
    t1 = Tenant(nome_fantasia="T1", status="ativa", max_users=5, created_at=now)
    t2 = Tenant(nome_fantasia="T2", status="ativa", max_users=5, created_at=now)
    db.add(t1)
    db.add(t2)
    db.flush()
    db.add(AuditLog(tenant_id=t1.id, action="user.create", created_at=now))
    db.add(AuditLog(tenant_id=t2.id, action="user.create", created_at=now))
    db.commit()
    t1id = t1.id
    db.close()

    resp = client.get(f"/api/platform/audit-logs?tenant_id={t1id}", headers=_platform_token())
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["tenant_id"] == t1id


def test_audit_logs_pagination(client):
    db = _Session()
    now = datetime.now(timezone.utc)
    tenant = Tenant(nome_fantasia="T", status="ativa", max_users=5, created_at=now)
    db.add(tenant)
    db.flush()
    for i in range(5):
        db.add(AuditLog(tenant_id=tenant.id, action=f"action.{i}", created_at=now))
    db.commit()
    db.close()

    resp = client.get("/api/platform/audit-logs?page=1&page_size=3", headers=_platform_token())
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert len(body["items"]) == 3
    assert body["page"] == 1
