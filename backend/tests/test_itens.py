import os
from decimal import Decimal

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
    return {"sub": "estabelecimento"}


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
# Helpers
# ---------------------------------------------------------------------------

def _criar_simples(c, nome="Insumo A", vendavel=False, custo_medio=None):
    payload = {"nome": nome, "tipo": "simples", "vendavel": vendavel, "unidade_base": "un"}
    resp = c.post("/api/itens", json=payload)
    assert resp.status_code == 201, resp.text
    iid = resp.json()["id"]
    if custo_medio is not None:
        db = _TestingSession()
        from src.models.itens import Item
        item = db.get(Item, iid)
        item.custo_medio = Decimal(str(custo_medio))
        db.commit()
        db.close()
    return resp.json()


# ---------------------------------------------------------------------------
# Item simples
# ---------------------------------------------------------------------------


def test_criar_item_simples(crud_client):
    resp = crud_client.post("/api/itens", json={
        "nome": "Coca Lata",
        "tipo": "simples",
        "vendavel": True,
        "unidade_base": "un",
        "preco_venda": "8.00",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["nome"] == "Coca Lata"
    assert body["tipo"] == "simples"
    assert body["ativo"] is True
    assert body["custo_composto"] is None


def test_item_simples_sem_ficha(crud_client):
    resp = crud_client.post("/api/itens", json={
        "nome": "Insumo",
        "tipo": "simples",
        "vendavel": False,
        "unidade_base": "g",
    })
    assert resp.status_code == 201
    assert resp.json()["componentes"] is None


# ---------------------------------------------------------------------------
# Validações de domínio
# ---------------------------------------------------------------------------


def test_preco_em_nao_vendavel(crud_client):
    resp = crud_client.post("/api/itens", json={
        "nome": "Insumo X",
        "tipo": "simples",
        "vendavel": False,
        "unidade_base": "un",
        "preco_venda": "10.00",
    })
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "PRECO_EM_NAO_VENDAVEL"


def test_ficha_vazia_bloqueia(crud_client):
    resp = crud_client.post("/api/itens", json={
        "nome": "Composto sem ficha",
        "tipo": "composto",
        "vendavel": True,
        "unidade_base": "un",
        "preco_venda": "20.00",
        "ficha_tecnica": [],
    })
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "FICHA_VAZIA"


def test_ficha_aninhada_bloqueada(crud_client):
    insumo = _criar_simples(crud_client, "Insumo A")
    composto1_resp = crud_client.post("/api/itens", json={
        "nome": "Composto 1",
        "tipo": "composto",
        "vendavel": True,
        "unidade_base": "un",
        "preco_venda": "15.00",
        "ficha_tecnica": [{"insumo_id": insumo["id"], "quantidade": "1"}],
    })
    assert composto1_resp.status_code == 201
    c1_id = composto1_resp.json()["id"]

    resp = crud_client.post("/api/itens", json={
        "nome": "Composto 2 aninhado",
        "tipo": "composto",
        "vendavel": True,
        "unidade_base": "un",
        "preco_venda": "30.00",
        "ficha_tecnica": [{"insumo_id": c1_id, "quantidade": "1"}],
    })
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "FICHA_ANINHADA_NAO_SUPORTADA"


# ---------------------------------------------------------------------------
# Item composto + custo calculado
# ---------------------------------------------------------------------------


def test_criar_item_composto_com_ficha(crud_client):
    insumo = _criar_simples(crud_client, "Pão", custo_medio=2.0)
    carne = _criar_simples(crud_client, "Carne", custo_medio=10.0)

    resp = crud_client.post("/api/itens", json={
        "nome": "X-Burguer",
        "tipo": "composto",
        "vendavel": True,
        "unidade_base": "un",
        "preco_venda": "28.00",
        "ficha_tecnica": [
            {"insumo_id": insumo["id"], "quantidade": "1"},
            {"insumo_id": carne["id"], "quantidade": "2"},
        ],
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["tipo"] == "composto"
    assert len(body["componentes"]) == 2


def test_custo_composto_calculado(crud_client):
    insumo1 = _criar_simples(crud_client, "A", custo_medio=5.0)
    insumo2 = _criar_simples(crud_client, "B", custo_medio=3.0)

    resp = crud_client.post("/api/itens", json={
        "nome": "Combo",
        "tipo": "composto",
        "vendavel": True,
        "unidade_base": "un",
        "preco_venda": "20.00",
        "ficha_tecnica": [
            {"insumo_id": insumo1["id"], "quantidade": "2"},
            {"insumo_id": insumo2["id"], "quantidade": "3"},
        ],
    })
    assert resp.status_code == 201
    body = resp.json()
    # custo = 2×5 + 3×3 = 10 + 9 = 19
    assert float(body["custo_composto"]) == pytest.approx(19.0)
    # cmv = 19/20 × 100 = 95%
    assert float(body["cmv_percentual"]) == pytest.approx(95.0, rel=0.01)


# ---------------------------------------------------------------------------
# Soft delete
# ---------------------------------------------------------------------------


def test_soft_delete_item_referenciado(crud_client):
    insumo = _criar_simples(crud_client, "Insumo Ref")
    crud_client.post("/api/itens", json={
        "nome": "Composto",
        "tipo": "composto",
        "vendavel": True,
        "unidade_base": "un",
        "preco_venda": "10.00",
        "ficha_tecnica": [{"insumo_id": insumo["id"], "quantidade": "1"}],
    })

    resp = crud_client.delete(f"/api/itens/{insumo['id']}")
    assert resp.status_code == 204

    # Inativo some da lista
    lista = crud_client.get("/api/itens").json()
    ids = [i["id"] for i in lista]
    assert insumo["id"] not in ids

    # Mas ainda existe no banco (ativo=False)
    detail = crud_client.get(f"/api/itens/{insumo['id']}").json()
    assert detail["ativo"] is False


def test_hard_delete_sem_referencia(crud_client):
    item = _criar_simples(crud_client, "Sem Ref")
    resp = crud_client.delete(f"/api/itens/{item['id']}")
    assert resp.status_code == 204

    resp2 = crud_client.get(f"/api/itens/{item['id']}")
    assert resp2.status_code == 404


# ---------------------------------------------------------------------------
# Filtros + lista
# ---------------------------------------------------------------------------


def test_filtros_tipo(crud_client):
    _criar_simples(crud_client, "Simples 1")
    insumo = _criar_simples(crud_client, "Insumo")
    crud_client.post("/api/itens", json={
        "nome": "Composto 1",
        "tipo": "composto",
        "vendavel": True,
        "unidade_base": "un",
        "preco_venda": "10.00",
        "ficha_tecnica": [{"insumo_id": insumo["id"], "quantidade": "1"}],
    })

    simples = crud_client.get("/api/itens?tipo=simples").json()
    compostos = crud_client.get("/api/itens?tipo=composto").json()
    assert all(i["tipo"] == "simples" for i in simples)
    assert all(i["tipo"] == "composto" for i in compostos)


def test_inativo_some_da_lista(crud_client):
    item = _criar_simples(crud_client, "Para inativar")
    crud_client.delete(f"/api/itens/{item['id']}")
    lista = crud_client.get("/api/itens").json()
    assert not any(i["id"] == item["id"] for i in lista)


def test_not_found(crud_client):
    resp = crud_client.get("/api/itens/9999")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"

    resp = crud_client.put("/api/itens/9999", json={
        "nome": "X", "tipo": "simples", "vendavel": False, "unidade_base": "un"
    })
    assert resp.status_code == 404
