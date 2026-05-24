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
from src.services.seed_service import run_seed

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


@pytest.fixture
def no_auth_client():
    def override_get_db():
        db = _TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------


def test_seed_idempotente():
    """run_seed twice produces same row count."""
    db = _TestingSession()
    run_seed(db)
    run_seed(db)

    from src.repositories.categorias_repository import list_all as list_cats
    from src.repositories.metodos_pagamento_repository import list_all as list_metodos

    cats = list_cats(db)
    metodos = list_metodos(db)
    db.close()

    assert len([c for c in cats if c.nome == "Geral"]) == 1
    assert len([m for m in metodos if m.nome == "PIX"]) == 1
    assert len(metodos) == 4


# ---------------------------------------------------------------------------
# Categorias
# ---------------------------------------------------------------------------


def test_categoria_crud(crud_client):
    """Create, list, update, delete categoria."""
    resp = crud_client.post("/api/categorias", json={"nome": "Bebidas"})
    assert resp.status_code == 201
    cat_id = resp.json()["id"]
    assert resp.json()["nome"] == "Bebidas"

    resp = crud_client.get("/api/categorias")
    assert resp.status_code == 200
    assert any(c["nome"] == "Bebidas" for c in resp.json())

    resp = crud_client.put(f"/api/categorias/{cat_id}", json={"nome": "Bebidas Alcoólicas"})
    assert resp.status_code == 200
    assert resp.json()["nome"] == "Bebidas Alcoólicas"

    resp = crud_client.delete(f"/api/categorias/{cat_id}")
    assert resp.status_code == 204

    resp = crud_client.get("/api/categorias")
    assert not any(c["id"] == cat_id for c in resp.json())


def test_categoria_not_found(crud_client):
    resp = crud_client.put("/api/categorias/9999", json={"nome": "X"})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"

    resp = crud_client.delete("/api/categorias/9999")
    assert resp.status_code == 404


def test_categoria_requires_auth(no_auth_client):
    resp = no_auth_client.get("/api/categorias")
    assert resp.status_code == 401


def test_subcategoria_crud(crud_client):
    """Create parent → subcategory, list tree, delete blocks parent while children exist."""
    pai = crud_client.post("/api/categorias", json={"nome": "Bebidas"})
    assert pai.status_code == 201
    pai_id = pai.json()["id"]

    filho = crud_client.post("/api/categorias", json={"nome": "Alcoólicas", "parent_id": pai_id})
    assert filho.status_code == 201
    filho_data = filho.json()
    assert filho_data["parent_id"] == pai_id

    resp = crud_client.get("/api/categorias")
    assert resp.status_code == 200
    tree = resp.json()
    pai_node = next((c for c in tree if c["id"] == pai_id), None)
    assert pai_node is not None
    assert any(ch["id"] == filho_data["id"] for ch in pai_node["children"])

    # DELETE parent blocked while child exists
    resp = crud_client.delete(f"/api/categorias/{pai_id}")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "HAS_CHILDREN"

    # DELETE child first, then parent succeeds
    crud_client.delete(f"/api/categorias/{filho_data['id']}")
    resp = crud_client.delete(f"/api/categorias/{pai_id}")
    assert resp.status_code == 204


def test_subcategoria_max_nivel(crud_client):
    """3rd level is blocked with 422."""
    pai = crud_client.post("/api/categorias", json={"nome": "Nivel1"})
    filho = crud_client.post("/api/categorias", json={"nome": "Nivel2", "parent_id": pai.json()["id"]})
    neto = crud_client.post("/api/categorias", json={"nome": "Nivel3", "parent_id": filho.json()["id"]})
    assert neto.status_code == 422
    assert neto.json()["error"]["code"] == "NIVEL_MAX_ATINGIDO"


def test_resumo_anual_retorna_12_entradas(crud_client):
    """GET /api/dashboard/resumo-anual returns exactly 12 entries."""
    resp = crud_client.get("/api/dashboard/resumo-anual?ano=2026")
    assert resp.status_code == 200
    assert len(resp.json()) == 12


# ---------------------------------------------------------------------------
# Fornecedores
# ---------------------------------------------------------------------------


def test_fornecedor_crud(crud_client):
    """Create, list, update, delete fornecedor."""
    payload = {"nome": "Distribuidora ABC", "telefone": "11999990000", "email": "abc@test.com"}
    resp = crud_client.post("/api/fornecedores", json=payload)
    assert resp.status_code == 201
    fid = resp.json()["id"]
    assert resp.json()["telefone"] == "11999990000"

    resp = crud_client.get("/api/fornecedores")
    assert resp.status_code == 200
    assert any(f["nome"] == "Distribuidora ABC" for f in resp.json())

    resp = crud_client.put(f"/api/fornecedores/{fid}", json={"nome": "Dist. ABC Ltda", "telefone": None, "email": None})
    assert resp.status_code == 200
    assert resp.json()["nome"] == "Dist. ABC Ltda"
    assert resp.json()["telefone"] is None

    resp = crud_client.delete(f"/api/fornecedores/{fid}")
    assert resp.status_code == 204


def test_fornecedor_not_found(crud_client):
    resp = crud_client.put("/api/fornecedores/9999", json={"nome": "X"})
    assert resp.status_code == 404

    resp = crud_client.delete("/api/fornecedores/9999")
    assert resp.status_code == 404


def test_fornecedor_requires_auth(no_auth_client):
    resp = no_auth_client.get("/api/fornecedores")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Garçons
# ---------------------------------------------------------------------------


def test_garcom_crud(crud_client):
    """Create, list, update (toggle ativo) garçom."""
    resp = crud_client.post("/api/garcons", json={"nome": "João"})
    assert resp.status_code == 201
    gid = resp.json()["id"]
    assert resp.json()["ativo"] is True

    resp = crud_client.get("/api/garcons")
    assert resp.status_code == 200
    assert any(g["nome"] == "João" for g in resp.json())

    resp = crud_client.put(f"/api/garcons/{gid}", json={"nome": "João", "ativo": False})
    assert resp.status_code == 200
    assert resp.json()["ativo"] is False

    resp = crud_client.get("/api/garcons")
    garcom = next(g for g in resp.json() if g["id"] == gid)
    assert garcom["ativo"] is False


def test_garcom_inativo_aparece_na_lista(crud_client):
    """Garçom inativo deve aparecer na listagem (contrato para Issue 6)."""
    resp = crud_client.post("/api/garcons", json={"nome": "Maria"})
    gid = resp.json()["id"]
    crud_client.put(f"/api/garcons/{gid}", json={"nome": "Maria", "ativo": False})

    resp = crud_client.get("/api/garcons")
    ids = [g["id"] for g in resp.json()]
    assert gid in ids


def test_garcom_not_found(crud_client):
    resp = crud_client.put("/api/garcons/9999", json={"nome": "X", "ativo": True})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_garcom_requires_auth(no_auth_client):
    resp = no_auth_client.get("/api/garcons")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Métodos de Pagamento
# ---------------------------------------------------------------------------


def test_metodo_crud(crud_client):
    """Create, list, update (toggle ativo) método de pagamento."""
    resp = crud_client.post("/api/metodos-pagamento", json={"nome": "Vale Refeição"})
    assert resp.status_code == 201
    mid = resp.json()["id"]
    assert resp.json()["ativo"] is True

    resp = crud_client.get("/api/metodos-pagamento")
    assert resp.status_code == 200
    assert any(m["nome"] == "Vale Refeição" for m in resp.json())

    resp = crud_client.put(f"/api/metodos-pagamento/{mid}", json={"nome": "Vale Refeição", "ativo": False})
    assert resp.status_code == 200
    assert resp.json()["ativo"] is False


def test_metodo_not_found(crud_client):
    resp = crud_client.put("/api/metodos-pagamento/9999", json={"nome": "X", "ativo": True})
    assert resp.status_code == 404


def test_metodo_requires_auth(no_auth_client):
    resp = no_auth_client.get("/api/metodos-pagamento")
    assert resp.status_code == 401
