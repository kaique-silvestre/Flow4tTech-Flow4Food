import datetime
import os
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests")
os.environ.setdefault("ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine, update
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


def _criar_item(c, nome="Item", preco="50.00"):
    resp = c.post("/api/produtos", json={"nome": nome, "preco_venda": preco})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _criar_metodo(c, nome="PIX"):
    resp = c.post("/api/metodos-pagamento", json={"nome": nome})
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


def _abrir_comanda(c, garcom_id, identificacao="Mesa 1"):
    resp = c.post(
        "/api/comandas",
        json={"identificacao": identificacao, "tipo_identificacao": "mesa", "garcom_id": garcom_id},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _lancar_item(c, comanda_id, item_id, version, quantidade=1, cortesia=False):
    resp = c.post(
        f"/api/comandas/{comanda_id}/itens",
        json={"item_id": item_id, "quantidade": quantidade, "version": version, "cortesia": cortesia},
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


def _set_custo_medio(insumo_id: int, custo: Decimal) -> None:
    from src.models.insumos import Insumo

    db: Session = _TestingSession()
    try:
        db.execute(update(Insumo).where(Insumo.id == insumo_id).values(custo_medio=custo))
        db.commit()
    finally:
        db.close()


def _set_data_fechamento(comanda_id: int, dt_utc: datetime.datetime) -> None:
    from src.models.comandas import Comanda

    db: Session = _TestingSession()
    try:
        db.execute(update(Comanda).where(Comanda.id == comanda_id).values(data_fechamento=dt_utc))
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_dashboard_cards_hoje(c):
    """Fecha comanda R$100 hoje → faturamento_hoje=100, ticket_medio=100, comandas_fechadas_hoje=1."""
    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="100.00")
    metodo = _criar_metodo(c)

    comanda = _abrir_comanda(c, garcom["id"])
    _lancar_item(c, comanda["id"], item["id"], comanda["version"])
    _fechar(c, comanda["id"], metodo["id"], "100.00")

    resp = c.get("/api/dashboard")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert float(data["faturamento_hoje"]) == pytest.approx(100.0)
    assert float(data["ticket_medio_hoje"]) == pytest.approx(100.0)
    assert data["comandas_fechadas_hoje"] == 1


def test_dashboard_lucro_estimado(c):
    """Produto com insumo custo_medio=30, preco=100 → lucro_estimado = 70."""
    garcom = _criar_garcom(c)
    metodo = _criar_metodo(c)

    insumo_resp = c.post("/api/insumos", json={"nome": "Insumo CMV", "unidade_base": "un"})
    assert insumo_resp.status_code == 201
    insumo_id = insumo_resp.json()["id"]
    _set_custo_medio(insumo_id, Decimal("30.00"))

    produto_resp = c.post("/api/produtos", json={
        "nome": "Produto CMV", "preco_venda": "100.00",
        "ficha_tecnica": [{"insumo_id": insumo_id, "quantidade": "1"}],
    })
    assert produto_resp.status_code == 201
    produto = produto_resp.json()

    comanda = _abrir_comanda(c, garcom["id"])
    _lancar_item(c, comanda["id"], produto["id"], comanda["version"])
    _fechar(c, comanda["id"], metodo["id"], "100.00")

    resp = c.get("/api/dashboard")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert float(data["lucro_estimado_hoje"]) == pytest.approx(70.0)


def test_dashboard_faturamento_por_hora_timezone(c):
    """
    Comanda fechada às 23:00 UTC = 20:00 SP (UTC-3).
    bucket[20].faturamento > 0, bucket[23].faturamento == 0.
    """
    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="50.00")
    metodo = _criar_metodo(c)

    comanda = _abrir_comanda(c, garcom["id"])
    _lancar_item(c, comanda["id"], item["id"], comanda["version"])
    _fechar(c, comanda["id"], metodo["id"], "50.00")

    # Forçar data_fechamento = hoje às 23:00 UTC (= 20:00 SP)
    import datetime
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("America/Sao_Paulo")
    today_sp = datetime.datetime.now(TZ).date()
    dt_utc = datetime.datetime(today_sp.year, today_sp.month, today_sp.day, 23, 0, 0)
    _set_data_fechamento(comanda["id"], dt_utc)

    resp = c.get("/api/dashboard")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    buckets = {b["hora"]: float(b["faturamento"]) for b in data["faturamento_por_hora"]}
    assert len(data["faturamento_por_hora"]) == 24
    assert buckets[20] == pytest.approx(50.0)
    assert buckets[23] == pytest.approx(0.0)


def test_dashboard_top_10_produtos(c):
    """3 itens com quantidades distintas → lista ordenada por quantidade desc."""
    garcom = _criar_garcom(c)
    item_a = _criar_item(c, nome="ItemA", preco="10.00")
    item_b = _criar_item(c, nome="ItemB", preco="10.00")
    item_c = _criar_item(c, nome="ItemC", preco="10.00")
    metodo = _criar_metodo(c)

    # comanda 1: 3x ItemA, 2x ItemB, 1x ItemC
    comanda = _abrir_comanda(c, garcom["id"])
    v = comanda["version"]
    r = _lancar_item(c, comanda["id"], item_a["id"], v, quantidade=3)
    v = r["version"]
    r = _lancar_item(c, comanda["id"], item_b["id"], v, quantidade=2)
    v = r["version"]
    _lancar_item(c, comanda["id"], item_c["id"], v, quantidade=1)
    _fechar(c, comanda["id"], metodo["id"], "60.00")

    resp = c.get("/api/dashboard")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    top = data["top_10_produtos"]
    assert len(top) >= 3
    nomes = [p["nome"] for p in top]
    # ItemA (3) deve ser primeiro
    assert nomes[0] == "ItemA"
    assert top[0]["quantidade"] == 3
    assert top[1]["quantidade"] == 2
    assert top[2]["quantidade"] == 1


def test_dashboard_comandas_abertas_lista(c):
    """2 comandas abertas com itens → lista retorna ambas com qtd_itens correto."""
    garcom = _criar_garcom(c)
    item = _criar_item(c)

    comanda1 = _abrir_comanda(c, garcom["id"], identificacao="Mesa 1")
    _lancar_item(c, comanda1["id"], item["id"], comanda1["version"], quantidade=2)

    comanda2 = _abrir_comanda(c, garcom["id"], identificacao="Mesa 2")
    r = _lancar_item(c, comanda2["id"], item["id"], comanda2["version"], quantidade=1)
    _lancar_item(c, comanda2["id"], item["id"], r["version"], quantidade=1)

    resp = c.get("/api/dashboard")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    lista = data["comandas_abertas_lista"]
    assert len(lista) == 2
    assert data["comandas_abertas"] == 2

    by_id = {c_item["id"]: c_item for c_item in lista}
    assert by_id[comanda1["id"]]["qtd_itens"] == 2
    assert by_id[comanda2["id"]]["qtd_itens"] == 2
