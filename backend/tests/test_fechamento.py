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
    return {"sub": "1", "user_id": 1, "tenant_id": 1, "permissions": ["cadastros", "comandas", "compras", "configuracoes", "dashboard", "estoque", "gestao_usuarios", "relatorios"]}


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


@pytest.fixture
def c_no_raise():
    def override_get_db():
        db = _TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _fake_user
    with TestClient(app, raise_server_exceptions=False) as client:
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
    body: dict = {"nome": nome}
    if preco is not None:
        body["preco_venda"] = preco
    resp = c.post("/api/produtos", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _criar_insumo(c, nome="Insumo", custo_medio=None):
    from src.models.insumos import Insumo as InsumoModel

    resp = c.post("/api/insumos", json={"nome": nome, "unidade_base": "un"})
    assert resp.status_code == 201, resp.text
    insumo = resp.json()
    if custo_medio is not None:
        db = _TestingSession()
        try:
            obj = db.get(InsumoModel, insumo["id"])
            if obj:
                obj.custo_medio = Decimal(str(custo_medio))
                db.commit()
        finally:
            db.close()
    return insumo


def _criar_metodo(c, nome="PIX"):
    resp = c.post("/api/metodos-pagamento", json={"nome": nome})
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


def _abrir_comanda(c, garcom_id, identificacao="Mesa 1", pessoas=None):
    body = {"identificacao": identificacao, "tipo_identificacao": "mesa", "garcom_id": garcom_id}
    body["pessoas"] = pessoas if pessoas else ["Cliente 1"]
    resp = c.post("/api/comandas", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _lancar_item(c, comanda_id, item_id, version, quantidade=1, cortesia=False):
    resp = c.post(
        f"/api/comandas/{comanda_id}/itens",
        json={"item_id": item_id, "quantidade": quantidade, "version": version, "cortesia": cortesia},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _cancelar_item(c, comanda_id, item_comanda_id, version):
    resp = c.post(
        f"/api/comandas/{comanda_id}/itens/{item_comanda_id}/cancelar",
        json={"motivo": "erro_lancamento", "estornado": False, "version": version},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _fechar(c, comanda_id, metodo_id, valor, modo="sem_divisao"):
    return c.post(
        f"/api/comandas/{comanda_id}/fechar",
        json={"pagamentos": [{"metodo_id": metodo_id, "valor": str(valor)}], "modo_divisao": modo},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_subtotal_exclui_cancelados(c):
    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="30.00")
    metodo = _criar_metodo(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]

    r1 = _lancar_item(c, cid, item["id"], comanda["version"])
    item_comanda_id = r1["itens_ativos"][0]["id"]
    r2 = _lancar_item(c, cid, item["id"], r1["version"])
    r3 = _cancelar_item(c, cid, item_comanda_id, r2["version"])
    assert float(r3["total_parcial"]) == 30.0

    resp = _fechar(c, cid, metodo["id"], "30.00")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "fechada"
    assert float(data["total"]) == 30.0


def test_cortesia_nao_some_subtotal_mas_baixa_estoque(c):
    """Cortesia: preco_unitario=0 nao some no subtotal, mas baixa de estoque eh feita (CMV)."""
    from src.models.movimentos_estoque import MovimentoEstoque, TipoMovimento

    garcom = _criar_garcom(c)
    metodo = _criar_metodo(c)

    insumo_cortesia = _criar_insumo(c, nome="Insumo Cortesia")
    insumo_normal = _criar_insumo(c, nome="Insumo Normal")

    item_cortesia = c.post("/api/produtos", json={
        "nome": "Cortesia", "preco_venda": "10.00",
        "ficha_tecnica": [{"insumo_id": insumo_cortesia["id"], "quantidade": "1"}],
    }).json()
    item_normal = c.post("/api/produtos", json={
        "nome": "Normal", "preco_venda": "30.00",
        "ficha_tecnica": [{"insumo_id": insumo_normal["id"], "quantidade": "1"}],
    }).json()

    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]

    r1 = _lancar_item(c, cid, item_cortesia["id"], comanda["version"], cortesia=True)
    assert float(r1["total_parcial"]) == 0.0

    r2 = _lancar_item(c, cid, item_normal["id"], r1["version"])
    assert float(r2["total_parcial"]) == 30.0

    resp = _fechar(c, cid, metodo["id"], "30.00")
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "fechada"

    db: Session = _TestingSession()
    try:
        movimentos = db.query(MovimentoEstoque).filter(
            MovimentoEstoque.tipo == TipoMovimento.SAIDA_VENDA.value
        ).all()
        assert len(movimentos) == 2
        insumo_ids_baixados = {m.insumo_id for m in movimentos}
        assert insumo_cortesia["id"] in insumo_ids_baixados
        assert insumo_normal["id"] in insumo_ids_baixados
    finally:
        db.close()


def test_fechar_com_desconto_percentual(c):
    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="100.00")
    metodo = _criar_metodo(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]

    _lancar_item(c, cid, item["id"], comanda["version"])
    resp_desc = c.post(f"/api/comandas/{cid}/desconto", json={"desconto_percentual": "10"})
    assert resp_desc.status_code == 200, resp_desc.text

    resp = _fechar(c, cid, metodo["id"], "90.00")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "fechada"
    assert float(data["total"]) == pytest.approx(90.0, abs=0.01)
    assert float(data["desconto_percentual"]) == 10.0


def test_fechar_com_desconto_valor(c):
    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="100.00")
    metodo = _criar_metodo(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]

    _lancar_item(c, cid, item["id"], comanda["version"])
    resp_desc = c.post(f"/api/comandas/{cid}/desconto", json={"desconto_valor": "8.90"})
    assert resp_desc.status_code == 200, resp_desc.text

    resp = _fechar(c, cid, metodo["id"], "91.10")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "fechada"
    assert float(data["total"]) == pytest.approx(91.10, abs=0.01)


def test_pagamento_nao_bate_retorna_400(c):
    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="90.00")
    metodo = _criar_metodo(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]

    _lancar_item(c, cid, item["id"], comanda["version"])
    resp = _fechar(c, cid, metodo["id"], "80.00")  # deveria ser 90
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "PAGAMENTO_NAO_BATE"
    # comanda permanece aberta
    assert c.get(f"/api/comandas/{cid}").json()["status"] == "aberta"


def test_fechar_parcial_mantem_aberta(c):
    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="90.00")
    metodo = _criar_metodo(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]

    _lancar_item(c, cid, item["id"], comanda["version"])
    resp = _fechar(c, cid, metodo["id"], "50.00", modo="parcial")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "aberta"
    assert float(data["saldo_pendente"]) == pytest.approx(40.0, abs=0.01)


def test_fechar_parcial_calculado_sem_desconto(c):
    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="100.00")
    metodo = _criar_metodo(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]

    _lancar_item(c, cid, item["id"], comanda["version"])
    # desconto 20% => total final seria 80, mas parcial usa subtotal=100
    c.post(f"/api/comandas/{cid}/desconto", json={"desconto_percentual": "20"})

    # parcial de 60 sobre base 100 eh valido
    resp = _fechar(c, cid, metodo["id"], "60.00", modo="parcial")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "aberta"
    assert float(data["saldo_pendente"]) == pytest.approx(40.0, abs=0.01)


def test_divisao_por_pessoa_sem_pessoas_retorna_400(c):
    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="50.00")
    metodo = _criar_metodo(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]

    _lancar_item(c, cid, item["id"], comanda["version"])
    resp = _fechar(c, cid, metodo["id"], "50.00", modo="por_pessoa")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "PESSOAS_INSUFICIENTES"


def test_baixa_estoque_item_simples(c):
    from src.models.insumos import Insumo as InsumoModel
    from src.models.movimentos_estoque import MovimentoEstoque, TipoMovimento

    garcom = _criar_garcom(c)
    metodo = _criar_metodo(c)

    insumo = _criar_insumo(c, nome="Insumo Simples")
    insumo_id = insumo["id"]

    produto_resp = c.post("/api/produtos", json={
        "nome": "Produto Simples", "preco_venda": "30.00",
        "ficha_tecnica": [{"insumo_id": insumo_id, "quantidade": "1"}],
    })
    assert produto_resp.status_code == 201, produto_resp.text
    produto_id = produto_resp.json()["id"]

    db: Session = _TestingSession()
    try:
        insumo_obj = db.get(InsumoModel, insumo_id)
        insumo_obj.estoque_atual = Decimal("10")
        db.commit()
    finally:
        db.close()

    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]
    _lancar_item(c, cid, produto_id, comanda["version"], quantidade=3)

    resp = _fechar(c, cid, metodo["id"], "90.00")
    assert resp.status_code == 200, resp.text

    db = _TestingSession()
    try:
        insumo_obj = db.get(InsumoModel, insumo_id)
        assert float(insumo_obj.estoque_atual) == pytest.approx(7.0, abs=0.001)
        mov = (
            db.query(MovimentoEstoque)
            .filter(MovimentoEstoque.insumo_id == insumo_id, MovimentoEstoque.tipo == TipoMovimento.SAIDA_VENDA.value)
            .first()
        )
        assert mov is not None
        assert float(mov.quantidade) == pytest.approx(3.0, abs=0.001)
    finally:
        db.close()


def test_baixa_estoque_composto_explode_ficha(c):
    from src.models.insumos import Insumo as InsumoModel
    from src.models.movimentos_estoque import MovimentoEstoque, TipoMovimento

    garcom = _criar_garcom(c)
    metodo = _criar_metodo(c)

    insumo1 = _criar_insumo(c, nome="Pao")
    insumo2 = _criar_insumo(c, nome="Carne")

    resp_produto = c.post("/api/produtos", json={
        "nome": "Burguer", "preco_venda": "20.00",
        "ficha_tecnica": [
            {"insumo_id": insumo1["id"], "quantidade": "1"},
            {"insumo_id": insumo2["id"], "quantidade": "0.2"},
        ],
    })
    assert resp_produto.status_code == 201, resp_produto.text
    produto = resp_produto.json()

    db: Session = _TestingSession()
    try:
        obj1 = db.get(InsumoModel, insumo1["id"])
        obj2 = db.get(InsumoModel, insumo2["id"])
        obj1.estoque_atual = Decimal("10")
        obj2.estoque_atual = Decimal("5")
        db.commit()
    finally:
        db.close()

    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]
    _lancar_item(c, cid, produto["id"], comanda["version"], quantidade=2)

    resp = _fechar(c, cid, metodo["id"], "40.00")
    assert resp.status_code == 200, resp.text

    db = _TestingSession()
    try:
        obj1 = db.get(InsumoModel, insumo1["id"])
        obj2 = db.get(InsumoModel, insumo2["id"])
        assert float(obj1.estoque_atual) == pytest.approx(8.0, abs=0.001)
        assert float(obj2.estoque_atual) == pytest.approx(4.6, abs=0.001)
        movimentos = (
            db.query(MovimentoEstoque)
            .filter(MovimentoEstoque.tipo == TipoMovimento.SAIDA_VENDA.value)
            .all()
        )
        assert len(movimentos) == 2
    finally:
        db.close()


def test_atomicidade_falha_nao_persiste(c_no_raise):
    import unittest.mock as mock

    from src.models.pagamentos import Pagamento

    garcom = _criar_garcom(c_no_raise)
    item = _criar_item(c_no_raise, preco="50.00")
    metodo = _criar_metodo(c_no_raise)
    comanda = _abrir_comanda(c_no_raise, garcom["id"])
    cid = comanda["id"]
    _lancar_item(c_no_raise, cid, item["id"], comanda["version"])

    with mock.patch(
        "src.services.comandas_service._dar_baixa_estoque",
        side_effect=RuntimeError("falha simulada"),
    ):
        resp = _fechar(c_no_raise, cid, metodo["id"], "50.00")
        assert resp.status_code == 500

    assert c_no_raise.get(f"/api/comandas/{cid}").json()["status"] == "aberta"

    db: Session = _TestingSession()
    try:
        count = db.query(Pagamento).filter(Pagamento.comanda_id == cid).count()
        assert count == 0
    finally:
        db.close()
