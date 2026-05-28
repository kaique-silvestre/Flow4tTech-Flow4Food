"""Issue 2 — CAS (optimistic locking) tests for aplicar_desconto and cancelar_comanda."""

import os
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

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


def _fake_user() -> dict:
    return {
        "sub": "1",
        "user_id": 1,
        "tenant_id": 1,
        "permissions": ["comandas", "cadastros", "estoque", "compras", "configuracoes", "dashboard", "gestao_usuarios", "relatorios"],
    }


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


@pytest.fixture
def client():
    def override_db():
        db = _Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = _fake_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _criar_garcom(c):
    r = c.post("/api/garcons", json={"nome": "Garcom CAS"})
    assert r.status_code == 201
    return r.json()["id"]


def _abrir_comanda(c, garcom_id):
    r = c.post("/api/comandas", json={
        "identificacao": "Mesa CAS",
        "tipo_identificacao": "mesa",
        "garcom_id": garcom_id,
        "pessoas": ["A"],
    })
    assert r.status_code == 201
    return r.json()


def test_aplicar_desconto_versao_stale_retorna_409(client):
    garcom_id = _criar_garcom(client)
    comanda = _abrir_comanda(client, garcom_id)
    comanda_id = comanda["id"]
    version_atual = comanda["version"]

    # Stale version = version_atual - 1 (or any wrong value)
    stale_version = version_atual - 1
    r = client.post(
        f"/api/comandas/{comanda_id}/desconto",
        json={"version": stale_version, "desconto_percentual": "10.00"},
    )
    assert r.status_code == 409, r.text


def test_aplicar_desconto_versao_correta_sucesso(client):
    garcom_id = _criar_garcom(client)
    comanda = _abrir_comanda(client, garcom_id)
    comanda_id = comanda["id"]
    version_atual = comanda["version"]

    r = client.post(
        f"/api/comandas/{comanda_id}/desconto",
        json={"version": version_atual, "desconto_percentual": "10.00"},
    )
    assert r.status_code == 200, r.text
    assert Decimal(r.json()["desconto_percentual"]) == Decimal("10")


def test_cancelar_comanda_versao_stale_retorna_409(client):
    garcom_id = _criar_garcom(client)
    comanda = _abrir_comanda(client, garcom_id)
    comanda_id = comanda["id"]
    version_atual = comanda["version"]

    stale_version = version_atual - 1
    r = client.post(f"/api/comandas/{comanda_id}/cancelar", json={"version": stale_version})
    assert r.status_code == 409, r.text


def test_cancelar_comanda_versao_correta_sucesso(client):
    garcom_id = _criar_garcom(client)
    comanda = _abrir_comanda(client, garcom_id)
    comanda_id = comanda["id"]
    version_atual = comanda["version"]

    r = client.post(f"/api/comandas/{comanda_id}/cancelar", json={"version": version_atual})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "cancelada"
