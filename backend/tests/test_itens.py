import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests")
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
_TestingSession = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def _fake_user() -> dict:
    return {"sub": "1", "user_id": 1, "tenant_id": 1, "permissions": ["cadastros", "comandas", "compras", "configuracoes", "dashboard", "estoque", "gestao_usuarios", "relatorios"]}


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


@pytest.fixture
def crud_client():
    def override_get_db():
        db = _TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _fake_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# /api/itens foi removido — todos os endpoints retornam 404
# ---------------------------------------------------------------------------

def test_get_itens_retorna_404(crud_client):
    resp = crud_client.get("/api/itens")
    assert resp.status_code == 404
    assert "removido" in resp.json()["error"]["message"].lower() or \
           "/api/insumos" in resp.json()["error"]["message"]


def test_post_itens_retorna_404(crud_client):
    resp = crud_client.post("/api/itens", json={"nome": "X"})
    assert resp.status_code == 404


def test_get_item_por_id_retorna_404(crud_client):
    resp = crud_client.get("/api/itens/1")
    assert resp.status_code == 404


def test_put_item_retorna_404(crud_client):
    resp = crud_client.put("/api/itens/1", json={"nome": "X"})
    assert resp.status_code == 404


def test_delete_item_retorna_404(crud_client):
    resp = crud_client.delete("/api/itens/1")
    assert resp.status_code == 404


def test_get_top_itens_retorna_404(crud_client):
    resp = crud_client.get("/api/itens/top")
    assert resp.status_code == 404
