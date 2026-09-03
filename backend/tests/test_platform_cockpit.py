import os
from datetime import datetime, timezone
from unittest.mock import patch

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


def _platform_token() -> str:
    return create_access_token(
        {"platform_admin": True, "admin_id": 1, "email": "admin@platform.com"}
    )


def _tenant_token() -> str:
    return create_access_token({"user_id": 1, "tenant_id": 1, "permissions": []})


_SAMPLE_METRIC = {
    "id": 1,
    "nome_fantasia": "Empresa A",
    "cnpj": "00.000.000/0001-00",
    "status_tenant": "ativo",
    "status_assinatura": "ativa",
    "dias_cliente": 30,
    "ultimo_login": None,
    "comandas_mes": 10,
    "faturamento_mes": 1500.0,
    "usuarios_ativos_30d": 3,
    "compras_mes": 5,
}


# G1 — GET /api/platform/cockpit retorna lista de métricas
def test_get_cockpit_returns_list(client):
    with patch(
        "src.repositories.platform_repository.get_cockpit_metrics",
        return_value={"items": [_SAMPLE_METRIC], "total": 1, "page": 1, "page_size": 50, "total_pages": 1},
    ):
        resp = client.get(
            "/api/platform/cockpit",
            headers={"Authorization": f"Bearer {_platform_token()}"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == 1
    assert data["items"][0]["nome_fantasia"] == "Empresa A"
    assert data["items"][0]["comandas_mes"] == 10
    assert data["items"][0]["faturamento_mes"] == pytest.approx(1500.0)
    assert data["items"][0]["usuarios_ativos_30d"] == 3
    assert data["items"][0]["compras_mes"] == 5
    assert data["items"][0]["dias_cliente"] == 30


# G2 — filtro por status passa para repositório
def test_get_cockpit_passes_status_filter(client):
    captured = {}

    def fake_get_cockpit(db, status_filter=None, page=1, page_size=50):
        captured["status_filter"] = status_filter
        captured["page"] = page
        captured["page_size"] = page_size
        return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}

    with patch(
        "src.repositories.platform_repository.get_cockpit_metrics",
        side_effect=fake_get_cockpit,
    ):
        resp = client.get(
            "/api/platform/cockpit?status=trial&page=2&page_size=20",
            headers={"Authorization": f"Bearer {_platform_token()}"},
        )
    assert resp.status_code == 200
    assert captured["status_filter"] == "trial"
    assert captured["page"] == 2
    assert captured["page_size"] == 20


def test_get_cockpit_rejects_unsafe_page_size(client):
    resp = client.get(
        "/api/platform/cockpit?page_size=101",
        headers={"Authorization": f"Bearer {_platform_token()}"},
    )
    assert resp.status_code == 422


# G3 — GET /api/platform/tenants/{id}/cockpit retorna métricas do tenant
def test_get_tenant_cockpit_returns_metrics(client):
    with patch(
        "src.repositories.platform_repository.get_tenant_cockpit_metrics",
        return_value=_SAMPLE_METRIC,
    ):
        resp = client.get(
            "/api/platform/tenants/1/cockpit",
            headers={"Authorization": f"Bearer {_platform_token()}"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert data["faturamento_mes"] == pytest.approx(1500.0)


# G4 — tenant inexistente retorna 404
def test_get_tenant_cockpit_not_found(client):
    with patch(
        "src.repositories.platform_repository.get_tenant_cockpit_metrics",
        return_value=None,
    ):
        resp = client.get(
            "/api/platform/tenants/999/cockpit",
            headers={"Authorization": f"Bearer {_platform_token()}"},
        )
    assert resp.status_code == 404


# G5 — token de tenant rejeitado com 403 em /cockpit
def test_tenant_token_rejected_cockpit(client):
    resp = client.get(
        "/api/platform/cockpit",
        headers={"Authorization": f"Bearer {_tenant_token()}"},
    )
    assert resp.status_code == 403


# G6 — sem token retorna 401
def test_no_token_returns_401_cockpit(client):
    resp = client.get("/api/platform/cockpit")
    assert resp.status_code == 401


# G7 — sem token retorna 401 em tenant cockpit
def test_no_token_returns_401_tenant_cockpit(client):
    resp = client.get("/api/platform/tenants/1/cockpit")
    assert resp.status_code == 401
