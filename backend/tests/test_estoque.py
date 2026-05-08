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

def _criar_item(c, nome="Item A", tipo="simples", vendavel=False):
    payload = {"nome": nome, "unidade_base": "un"}
    resp = c.post("/api/insumos", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _comprar(c, item_id, quantidade, custo_total):
    payload = {
        "data_compra": "2026-05-07",
        "itens": [{"item_id": item_id, "quantidade": quantidade, "custo_total": custo_total}],
    }
    resp = c.post("/api/compras", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _baixa(c, item_id, quantidade, motivo="perda", observacao=None):
    payload = {"item_id": item_id, "quantidade": quantidade, "motivo": motivo}
    if observacao:
        payload["observacao"] = observacao
    return c.post("/api/estoque/baixa-sem-venda", json=payload)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_baixa_sem_venda_atualiza_saldo(crud_client):
    item = _criar_item(crud_client, "Coca Lata")
    _comprar(crud_client, item["id"], 100, 200.0)

    resp = _baixa(crud_client, item["id"], 10, "perda")
    assert resp.status_code == 201
    data = resp.json()
    assert data["saldo_negativo"] is False
    assert float(data["movimento"]["saldo_apos"]) == pytest.approx(90.0)
    assert data["movimento"]["tipo"] == "saida_perda"
    assert data["movimento"]["motivo"] == "perda"

    saldo = crud_client.get("/api/estoque/saldo").json()
    item_saldo = next(s for s in saldo if s["id"] == item["id"])
    assert float(item_saldo["estoque_atual"]) == pytest.approx(90.0)


def test_baixa_saldo_negativo_permitido(crud_client):
    item = _criar_item(crud_client, "Item Neg")

    resp = _baixa(crud_client, item["id"], 5, "consumo_interno")
    assert resp.status_code == 201
    data = resp.json()
    assert data["saldo_negativo"] is True
    assert float(data["movimento"]["saldo_apos"]) == pytest.approx(-5.0)


def test_baixa_produto_nao_encontrado(crud_client):
    resp = crud_client.post("/api/produtos", json={"nome": "Produto Y", "preco_venda": 10.0})
    assert resp.status_code == 201
    produto = resp.json()

    resp = _baixa(crud_client, produto["id"], 1)
    assert resp.status_code == 404


def test_historico_ordenado_desc(crud_client):
    item = _criar_item(crud_client, "Item Hist")
    _comprar(crud_client, item["id"], 50, 100.0)
    _baixa(crud_client, item["id"], 5, "cortesia")

    resp = crud_client.get("/api/estoque/movimentos")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    # Mais recente primeiro (saida_perda > entrada)
    assert data["itens"][0]["tipo"] == "saida_perda"
    assert data["itens"][1]["tipo"] == "entrada"


def test_historico_filtro_tipo(crud_client):
    item = _criar_item(crud_client, "Item Tipo")
    _comprar(crud_client, item["id"], 50, 100.0)
    _baixa(crud_client, item["id"], 5, "quebra")

    resp = crud_client.get("/api/estoque/movimentos?tipo=entrada")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["itens"][0]["tipo"] == "entrada"


def test_saldo_exclui_produtos(crud_client):
    _criar_item(crud_client, "Insumo Saldo")
    crud_client.post("/api/produtos", json={"nome": "Produto Saldo", "preco_venda": 15.0})

    resp = crud_client.get("/api/estoque/saldo")
    assert resp.status_code == 200
    nomes = [s["nome"] for s in resp.json()]
    assert "Insumo Saldo" in nomes
    assert "Produto Saldo" not in nomes


def test_saldo_filtro_busca(crud_client):
    _criar_item(crud_client, "Coca Cola")
    _criar_item(crud_client, "Fanta Laranja")

    resp = crud_client.get("/api/estoque/saldo?busca=coca")
    assert resp.status_code == 200
    nomes = [s["nome"] for s in resp.json()]
    assert "Coca Cola" in nomes
    assert "Fanta Laranja" not in nomes
