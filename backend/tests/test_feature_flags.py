"""Tests for issue #34 — Feature flags por tenant."""
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
from src.models.tenant_features import TenantFeature
from src.models.tenants import Tenant
from src.services.auth_service import create_access_token

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


def _tenant_token(tenant_id: int = 1, permissions: list = None) -> str:
    return create_access_token({
        "sub": "1",
        "user_id": 1,
        "tenant_id": tenant_id,
        "permissions": permissions or ["dashboard"],
        "subscription_status": "ativa",
    })


def _seed_tenant() -> int:
    db = _Session()
    now = datetime.now(timezone.utc)
    t = Tenant(nome_fantasia="Empresa", cnpj="00.000.000/0001-00", status="ativo", max_users=5, created_at=now)
    db.add(t)
    db.flush()
    tenant_id = t.id
    a = Assinatura(tenant_id=tenant_id, status="ativa", data_inicio=now, created_at=now, updated_at=now)
    db.add(a)
    db.commit()
    db.close()
    return tenant_id


def _add_feature(tenant_id: int, feature: str, enabled: bool) -> None:
    db = _Session()
    now = datetime.now(timezone.utc)
    db.add(TenantFeature(tenant_id=tenant_id, feature=feature, enabled=enabled, updated_at=now))
    db.commit()
    db.close()


class TestGetAppFeatures:
    def test_returns_empty_when_no_flags(self, client):
        t = _seed_tenant()
        token = _tenant_token(t)
        resp = client.get("/api/app/features", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_enabled_flag(self, client):
        t = _seed_tenant()
        _add_feature(t, "dashboard", True)
        token = _tenant_token(t)
        resp = client.get("/api/app/features", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["feature"] == "dashboard"
        assert data[0]["enabled"] is True

    def test_returns_disabled_flag(self, client):
        t = _seed_tenant()
        _add_feature(t, "relatorios", False)
        token = _tenant_token(t)
        resp = client.get("/api/app/features", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()[0]["enabled"] is False

    def test_returns_multiple_flags(self, client):
        t = _seed_tenant()
        _add_feature(t, "dashboard", True)
        _add_feature(t, "compras", False)
        _add_feature(t, "relatorios", True)
        token = _tenant_token(t)
        resp = client.get("/api/app/features", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_requires_auth(self, client):
        resp = client.get("/api/app/features")
        assert resp.status_code == 401


class TestRequireFeature:
    def test_allows_when_no_row(self, client):
        """No row in tenant_features = feature enabled by default."""
        t = _seed_tenant()
        token = _tenant_token(t, permissions=["dashboard"])
        resp = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})
        # dashboard route requires feature("dashboard") + permission("dashboard")
        # no feature row = allowed, so should not get 403 from feature check
        assert resp.status_code != 403

    def test_blocks_when_explicitly_disabled(self, client):
        t = _seed_tenant()
        _add_feature(t, "dashboard", False)
        token = _tenant_token(t, permissions=["dashboard"])
        resp = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_allows_when_explicitly_enabled(self, client):
        t = _seed_tenant()
        _add_feature(t, "dashboard", True)
        token = _tenant_token(t, permissions=["dashboard"])
        resp = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code != 403
