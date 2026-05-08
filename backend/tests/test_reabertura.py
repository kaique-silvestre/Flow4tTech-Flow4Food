import os
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests")
os.environ.setdefault("ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

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
def c():
    def override_get_db():
        db = _TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _fake_user
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _criar_garcom(c, nome="Garcom"):
    resp = c.post("/api/garcons", json={"nome": nome})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _criar_item(c, nome="Item", preco="50.00", tipo="simples", vendavel=True):
    body: dict = {"nome": nome, "tipo": tipo, "vendavel": vendavel, "unidade_base": "un"}
    if preco is not None:
        body["preco_venda"] = preco
    resp = c.post("/api/itens", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _criar_metodo(c, nome="PIX"):
    resp = c.post("/api/metodos-pagamento", json={"nome": nome})
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


def _abrir_comanda(c, garcom_id, identificacao="Mesa 1"):
    resp = c.post("/api/comandas", json={"identificacao": identificacao, "tipo_identificacao": "mesa", "garcom_id": garcom_id})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _lancar_item(c, comanda_id, item_id, version, quantidade=1):
    resp = c.post(
        f"/api/comandas/{comanda_id}/itens",
        json={"item_id": item_id, "quantidade": quantidade, "version": version},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _fechar(c, comanda_id, metodo_id, valor):
    resp = c.post(
        f"/api/comandas/{comanda_id}/fechar",
        json={"pagamentos": [{"metodo_id": metodo_id, "valor": str(valor)}], "modo_divisao": "sem_divisao"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _set_estoque(item_id: int, valor: float) -> None:
    from src.models.itens import Item
    db: Session = _TestingSession()
    try:
        it = db.get(Item, item_id)
        it.estoque_atual = Decimal(str(valor))  # type: ignore[union-attr]
        db.commit()
    finally:
        db.close()


def _get_estoque_db(item_id: int) -> float:
    from src.models.itens import Item
    db: Session = _TestingSession()
    try:
        it = db.get(Item, item_id)
        return float(it.estoque_atual) if it else 0.0  # type: ignore[union-attr]
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_reabrir_comanda_fechada_ok(c):
    from src.models.movimentos_estoque import MovimentoEstoque, TipoMovimento

    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="30.00")
    metodo = _criar_metodo(c)

    _set_estoque(item["id"], 10.0)

    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]
    _lancar_item(c, cid, item["id"], comanda["version"])
    _fechar(c, cid, metodo["id"], "30.00")

    assert pytest.approx(_get_estoque_db(item["id"]), abs=0.001) == 9.0

    resp = c.post(f"/api/comandas/{cid}/reabrir")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "reaberta"
    assert data["total"] is None
    assert data["data_fechamento"] is None

    assert pytest.approx(_get_estoque_db(item["id"]), abs=0.001) == 10.0

    # Deve haver movimento de estorno
    db: Session = _TestingSession()
    try:
        mov = (
            db.query(MovimentoEstoque)
            .filter(
                MovimentoEstoque.item_id == item["id"],
                MovimentoEstoque.tipo == TipoMovimento.ENTRADA_ESTORNO.value,
            )
            .first()
        )
        assert mov is not None
        assert float(mov.quantidade) == pytest.approx(1.0, abs=0.001)
    finally:
        db.close()


def test_reabrir_estorna_item_composto(c):
    garcom = _criar_garcom(c)
    insumo1 = _criar_item(c, nome="Insumo1", preco=None, tipo="simples", vendavel=False)
    insumo2 = _criar_item(c, nome="Insumo2", preco=None, tipo="simples", vendavel=False)

    # Composto criado com ficha_tecnica inline
    resp_composto = c.post("/api/itens", json={
        "nome": "Composto", "tipo": "composto", "vendavel": True,
        "unidade_base": "un", "preco_venda": "50.00",
        "ficha_tecnica": [
            {"insumo_id": insumo1["id"], "quantidade": "1"},
            {"insumo_id": insumo2["id"], "quantidade": "2"},
        ],
    })
    assert resp_composto.status_code == 201, resp_composto.text
    composto = resp_composto.json()
    metodo = _criar_metodo(c)

    _set_estoque(insumo1["id"], 10.0)
    _set_estoque(insumo2["id"], 10.0)

    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]
    _lancar_item(c, cid, composto["id"], comanda["version"], quantidade=2)
    _fechar(c, cid, metodo["id"], "100.00")

    # Após fechar: insumo1 -= 2 (1*2), insumo2 -= 4 (2*2)
    assert pytest.approx(_get_estoque_db(insumo1["id"]), abs=0.001) == 8.0
    assert pytest.approx(_get_estoque_db(insumo2["id"]), abs=0.001) == 6.0

    resp = c.post(f"/api/comandas/{cid}/reabrir")
    assert resp.status_code == 200, resp.text

    # Após reabrir: estoques restaurados
    assert pytest.approx(_get_estoque_db(insumo1["id"]), abs=0.001) == 10.0
    assert pytest.approx(_get_estoque_db(insumo2["id"]), abs=0.001) == 10.0


def test_reabrir_comanda_aberta_retorna_400(c):
    garcom = _criar_garcom(c)
    comanda = _abrir_comanda(c, garcom["id"])
    resp = c.post(f"/api/comandas/{comanda['id']}/reabrir")
    assert resp.status_code == 400, resp.text
    assert resp.json()["error"]["code"] == "COMANDA_NAO_FECHADA"


def test_reabrir_comanda_parcial_retorna_400(c):
    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="100.00")
    metodo = _criar_metodo(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]
    _lancar_item(c, cid, item["id"], comanda["version"])

    # Pagamento parcial → status permanece "aberta"
    resp = c.post(
        f"/api/comandas/{cid}/fechar",
        json={"pagamentos": [{"metodo_id": metodo["id"], "valor": "50.00"}], "modo_divisao": "parcial"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "aberta"

    resp = c.post(f"/api/comandas/{cid}/reabrir")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "COMANDA_NAO_FECHADA"


def test_reabrir_comanda_inexistente_retorna_404(c):
    resp = c.post("/api/comandas/99999/reabrir")
    assert resp.status_code == 404, resp.text


def test_reaberta_aparece_na_lista_abertas(c):
    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="50.00")
    metodo = _criar_metodo(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]
    _lancar_item(c, cid, item["id"], comanda["version"])
    _fechar(c, cid, metodo["id"], "50.00")

    # Não deve aparecer na lista de abertas após fechar
    lista = c.get("/api/comandas").json()
    assert all(c["id"] != cid for c in lista)

    # Reabrir
    c.post(f"/api/comandas/{cid}/reabrir")

    # Deve aparecer na lista de abertas após reabrir
    lista = c.get("/api/comandas").json()
    assert any(c["id"] == cid for c in lista)
