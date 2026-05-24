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
# Helpers
# ---------------------------------------------------------------------------

def _criar_garcom(c, nome="Joao", ativo=True):
    resp = c.post("/api/garcons", json={"nome": nome})
    assert resp.status_code == 201, resp.text
    garcom = resp.json()
    if not ativo:
        resp2 = c.put(f"/api/garcons/{garcom['id']}", json={"nome": nome, "ativo": False})
        assert resp2.status_code == 200, resp2.text
        return resp2.json()
    return garcom


def _criar_item_vendavel(c, nome="Coca", preco="10.00"):
    resp = c.post("/api/produtos", json={
        "nome": nome,
        "preco_venda": preco,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def _abrir_comanda(c, garcom_id, identificacao="Mesa 1", tipo="mesa"):
    resp = c.post("/api/comandas", json={
        "identificacao": identificacao,
        "tipo_identificacao": tipo,
        "garcom_id": garcom_id,
        "pessoas": [],
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def _lancar_item(c, comanda_id, item_id, version, quantidade=1, cortesia=False):
    resp = c.post(f"/api/comandas/{comanda_id}/itens", json={
        "item_id": item_id,
        "quantidade": quantidade,
        "cortesia": cortesia,
        "version": version,
    })
    return resp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_abrir_comanda(crud_client):
    garcom = _criar_garcom(crud_client)
    resp = crud_client.post("/api/comandas", json={
        "identificacao": "Mesa 5",
        "tipo_identificacao": "mesa",
        "garcom_id": garcom["id"],
        "pessoas": ["Ana", "Bob"],
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "aberta"
    assert body["version"] == 1
    assert body["pessoas"] == ["Ana", "Bob"]
    assert body["garcom_nome"] == "Joao"


def test_garcom_inativo_bloqueado(crud_client):
    garcom = _criar_garcom(crud_client, ativo=False)
    resp = crud_client.post("/api/comandas", json={
        "identificacao": "Mesa 1",
        "tipo_identificacao": "mesa",
        "garcom_id": garcom["id"],
        "pessoas": [],
    })
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "GARCOM_INATIVO"


def test_lancar_item_snapshot_preco(crud_client):
    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client, preco="15.50")
    comanda = _abrir_comanda(crud_client, garcom["id"])

    resp = _lancar_item(crud_client, comanda["id"], item["id"], comanda["version"])
    assert resp.status_code == 200
    body = resp.json()
    itens = body["itens_ativos"]
    assert len(itens) == 1
    assert Decimal(itens[0]["preco_unitario"]) == Decimal("15.50")


def test_cortesia_preco_zero(crud_client):
    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client, preco="20.00")
    comanda = _abrir_comanda(crud_client, garcom["id"])

    resp = _lancar_item(crud_client, comanda["id"], item["id"], comanda["version"], cortesia=True)
    assert resp.status_code == 200
    body = resp.json()
    itens = body["itens_ativos"]
    assert Decimal(itens[0]["preco_unitario"]) == Decimal("0")
    assert Decimal(itens[0]["subtotal"]) == Decimal("0")


def test_lancar_incrementa_version(crud_client):
    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client)
    comanda = _abrir_comanda(crud_client, garcom["id"])
    assert comanda["version"] == 1

    resp = _lancar_item(crud_client, comanda["id"], item["id"], 1)
    assert resp.status_code == 200
    assert resp.json()["version"] == 2


def test_version_conflict_retorna_409(crud_client):
    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client)
    comanda = _abrir_comanda(crud_client, garcom["id"])

    resp = _lancar_item(crud_client, comanda["id"], item["id"], version=999)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "COMANDA_DESATUALIZADA"


def test_editar_item(crud_client):
    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client)
    comanda = _abrir_comanda(crud_client, garcom["id"])

    resp = _lancar_item(crud_client, comanda["id"], item["id"], comanda["version"], quantidade=2)
    assert resp.status_code == 200
    body = resp.json()
    item_id = body["itens_ativos"][0]["id"]
    version = body["version"]

    resp2 = crud_client.patch(
        f"/api/comandas/{comanda['id']}/itens/{item_id}",
        json={"quantidade": 5, "version": version},
    )
    assert resp2.status_code == 200
    assert Decimal(resp2.json()["itens_ativos"][0]["quantidade"]) == Decimal("5")


def test_cancelar_item(crud_client):
    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client, preco="10.00")
    comanda = _abrir_comanda(crud_client, garcom["id"])

    resp = _lancar_item(crud_client, comanda["id"], item["id"], comanda["version"])
    body = resp.json()
    item_c_id = body["itens_ativos"][0]["id"]
    version = body["version"]

    resp2 = crud_client.post(
        f"/api/comandas/{comanda['id']}/itens/{item_c_id}/cancelar",
        json={"motivo": "erro_lancamento", "estornado": False, "version": version},
    )
    assert resp2.status_code == 200
    body2 = resp2.json()
    cancelado = next(i for i in body2["itens_ativos"] if i["id"] == item_c_id)
    assert cancelado["cancelado"] is True
    assert Decimal(body2["total_parcial"]) == Decimal("0")


def test_eventos_gravados(crud_client):
    from src.models.eventos_comanda import EventoComanda

    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client)
    comanda = _abrir_comanda(crud_client, garcom["id"])
    _lancar_item(crud_client, comanda["id"], item["id"], comanda["version"])

    db = _TestingSession()
    eventos = db.query(EventoComanda).filter(EventoComanda.comanda_id == comanda["id"]).all()
    db.close()
    assert len(eventos) == 2
    tipos = {e.tipo for e in eventos}
    assert "comanda_aberta" in tipos
    assert "item_lancado" in tipos


def test_total_parcial_exclui_cancelados_e_cortesias(crud_client):
    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client, preco="10.00")
    comanda = _abrir_comanda(crud_client, garcom["id"])

    # lançar item normal (10.00)
    resp = _lancar_item(crud_client, comanda["id"], item["id"], comanda["version"])
    body = resp.json()
    version = body["version"]

    # lançar cortesia (0.00)
    resp2 = _lancar_item(crud_client, comanda["id"], item["id"], version, cortesia=True)
    body2 = resp2.json()
    version2 = body2["version"]

    # total deve ser 10.00 (normal) + 0 (cortesia) = 10.00
    assert Decimal(body2["total_parcial"]) == Decimal("10.00")

    # cancelar o item normal
    item_normal_id = body2["itens_ativos"][0]["id"]
    resp3 = crud_client.post(
        f"/api/comandas/{comanda['id']}/itens/{item_normal_id}/cancelar",
        json={"motivo": "erro_lancamento", "estornado": False, "version": version2},
    )
    assert resp3.status_code == 200
    assert Decimal(resp3.json()["total_parcial"]) == Decimal("0")


def test_top_itens(crud_client):
    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client, nome="Cerveja")
    comanda = _abrir_comanda(crud_client, garcom["id"])

    version = comanda["version"]
    for _ in range(3):
        resp = _lancar_item(crud_client, comanda["id"], item["id"], version)
        version = resp.json()["version"]

    resp = crud_client.get("/api/produtos/top?dias=7&limit=6")
    assert resp.status_code == 200
    nomes = [i["nome"] for i in resp.json()]
    assert "Cerveja" in nomes
