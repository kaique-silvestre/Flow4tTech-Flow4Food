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


def _criar_insumo(c, nome="Insumo"):
    resp = c.post("/api/insumos", json={"nome": nome, "unidade_base": "un"})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _criar_produto(c, nome="Produto", preco="50.00", ficha_tecnica=None):
    body: dict = {"nome": nome, "preco_venda": preco}
    if ficha_tecnica:
        body["ficha_tecnica"] = ficha_tecnica
    resp = c.post("/api/produtos", json=body)
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


def _set_estoque(insumo_id: int, valor: float) -> None:
    from src.models.insumos import Insumo

    db: Session = _TestingSession()
    try:
        obj = db.get(Insumo, insumo_id)
        obj.estoque_atual = Decimal(str(valor))  # type: ignore[union-attr]
        db.commit()
    finally:
        db.close()


def _get_estoque_db(insumo_id: int) -> float:
    from src.models.insumos import Insumo

    db: Session = _TestingSession()
    try:
        obj = db.get(Insumo, insumo_id)
        return float(obj.estoque_atual) if obj else 0.0  # type: ignore[union-attr]
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_reabrir_comanda_fechada_ok(c):
    from src.models.movimentos_estoque import MovimentoEstoque, TipoMovimento

    garcom = _criar_garcom(c)
    metodo = _criar_metodo(c)

    insumo = _criar_insumo(c, nome="Insumo A")
    _set_estoque(insumo["id"], 10.0)

    produto = _criar_produto(c, preco="30.00", ficha_tecnica=[{"insumo_id": insumo["id"], "quantidade": "1"}])

    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]
    _lancar_item(c, cid, produto["id"], comanda["version"])
    _fechar(c, cid, metodo["id"], "30.00")

    assert pytest.approx(_get_estoque_db(insumo["id"]), abs=0.001) == 9.0

    resp = c.post(f"/api/comandas/{cid}/reabrir")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "reaberta"
    assert data["total"] is None
    assert data["data_fechamento"] is None

    assert pytest.approx(_get_estoque_db(insumo["id"]), abs=0.001) == 10.0

    db: Session = _TestingSession()
    try:
        mov = (
            db.query(MovimentoEstoque)
            .filter(
                MovimentoEstoque.insumo_id == insumo["id"],
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
    metodo = _criar_metodo(c)

    insumo1 = _criar_insumo(c, nome="Insumo1")
    insumo2 = _criar_insumo(c, nome="Insumo2")
    _set_estoque(insumo1["id"], 10.0)
    _set_estoque(insumo2["id"], 10.0)

    produto = _criar_produto(c, nome="Composto", preco="50.00", ficha_tecnica=[
        {"insumo_id": insumo1["id"], "quantidade": "1"},
        {"insumo_id": insumo2["id"], "quantidade": "2"},
    ])

    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]
    _lancar_item(c, cid, produto["id"], comanda["version"], quantidade=2)
    _fechar(c, cid, metodo["id"], "100.00")

    assert pytest.approx(_get_estoque_db(insumo1["id"]), abs=0.001) == 8.0
    assert pytest.approx(_get_estoque_db(insumo2["id"]), abs=0.001) == 6.0

    resp = c.post(f"/api/comandas/{cid}/reabrir")
    assert resp.status_code == 200, resp.text

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
    produto = _criar_produto(c, preco="100.00")
    metodo = _criar_metodo(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]
    _lancar_item(c, cid, produto["id"], comanda["version"])

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
    produto = _criar_produto(c, preco="50.00")
    metodo = _criar_metodo(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]
    _lancar_item(c, cid, produto["id"], comanda["version"])
    _fechar(c, cid, metodo["id"], "50.00")

    lista = c.get("/api/comandas").json()
    assert all(cmd["id"] != cid for cmd in lista)

    c.post(f"/api/comandas/{cid}/reabrir")

    lista = c.get("/api/comandas").json()
    assert any(cmd["id"] == cid for cmd in lista)
