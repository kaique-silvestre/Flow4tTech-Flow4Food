import datetime
import os

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


def _criar_item(c, nome="Item", preco="50.00"):
    resp = c.post("/api/produtos", json={"nome": nome, "preco_venda": preco})
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


def _forcar_data_fechamento(comanda_id: int, dt: datetime.datetime) -> None:
    """Força data_fechamento para simular dia diferente de hoje."""
    from src.models.comandas import Comanda
    db: Session = _TestingSession()
    try:
        c = db.get(Comanda, comanda_id)
        c.data_fechamento = dt  # type: ignore[union-attr]
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_vendas_do_dia_retorna_apenas_fechadas_hoje(c):
    garcom = _criar_garcom(c)
    item = _criar_item(c)
    metodo = _criar_metodo(c)

    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]
    _lancar_item(c, cid, item["id"], comanda["version"])
    _fechar(c, cid, metodo["id"], "50.00")

    # Comanda aberta (não deve aparecer)
    _abrir_comanda(c, garcom["id"], "Mesa 2")

    resp = c.get("/api/relatorios/vendas-do-dia")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    ids = [cmd["id"] for cmd in data["comandas"]]
    assert cid in ids
    # Todas as comandas retornadas são fechadas
    for cmd in data["comandas"]:
        assert cmd["total"] is not None


def test_historico_filtra_por_periodo(c):
    garcom = _criar_garcom(c)
    item = _criar_item(c)
    metodo = _criar_metodo(c)

    # Comanda de hoje
    cmd_hoje = _abrir_comanda(c, garcom["id"], "Mesa 1")
    _lancar_item(c, cmd_hoje["id"], item["id"], cmd_hoje["version"])
    _fechar(c, cmd_hoje["id"], metodo["id"], "50.00")

    # Comanda de 10 dias atrás (forçar data_fechamento)
    cmd_antiga = _abrir_comanda(c, garcom["id"], "Mesa 2")
    _lancar_item(c, cmd_antiga["id"], item["id"], cmd_antiga["version"])
    _fechar(c, cmd_antiga["id"], metodo["id"], "50.00")
    dt_antiga = datetime.datetime.utcnow() - datetime.timedelta(days=10)
    _forcar_data_fechamento(cmd_antiga["id"], dt_antiga)

    hoje = datetime.date.today().isoformat()
    resp = c.get(f"/api/relatorios/historico-comandas?data_inicio={hoje}&data_fim={hoje}")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    ids = [cmd["id"] for cmd in data["comandas"]]
    assert cmd_hoje["id"] in ids
    assert cmd_antiga["id"] not in ids


def test_historico_filtra_por_garcom(c):
    garcom1 = _criar_garcom(c, "Garcom1")
    garcom2 = _criar_garcom(c, "Garcom2")
    item = _criar_item(c)
    metodo = _criar_metodo(c)

    cmd1 = _abrir_comanda(c, garcom1["id"], "Mesa 1")
    _lancar_item(c, cmd1["id"], item["id"], cmd1["version"])
    _fechar(c, cmd1["id"], metodo["id"], "50.00")

    cmd2 = _abrir_comanda(c, garcom2["id"], "Mesa 2")
    _lancar_item(c, cmd2["id"], item["id"], cmd2["version"])
    _fechar(c, cmd2["id"], metodo["id"], "50.00")

    hoje = datetime.date.today().isoformat()
    resp = c.get(f"/api/relatorios/historico-comandas?data_inicio={hoje}&data_fim={hoje}&garcom_id={garcom1['id']}")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    ids = [cmd["id"] for cmd in data["comandas"]]
    assert cmd1["id"] in ids
    assert cmd2["id"] not in ids


def test_fechamento_caixa_agrega_por_metodo(c):
    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="200.00")
    pix = _criar_metodo(c, "PIX")
    dinheiro = _criar_metodo(c, "Dinheiro")

    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]
    _lancar_item(c, cid, item["id"], comanda["version"])

    # O endpoint aceita lista de pagamentos em um único POST:
    resp = c.post(
        f"/api/comandas/{cid}/fechar",
        json={
            "pagamentos": [
                {"metodo_id": pix["id"], "valor": "120.00"},
                {"metodo_id": dinheiro["id"], "valor": "80.00"},
            ],
            "modo_divisao": "sem_divisao",
        },
    )
    assert resp.status_code == 200, resp.text

    hoje = datetime.date.today().isoformat()
    resp = c.get(f"/api/relatorios/fechamento-caixa?data={hoje}")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["qtd_comandas"] == 1
    assert float(data["faturamento_bruto"]) == pytest.approx(200.0)

    metodos = {m["metodo_nome"]: float(m["total"]) for m in data["por_metodo"]}
    assert "PIX" in metodos
    assert "Dinheiro" in metodos
    assert metodos["PIX"] == pytest.approx(120.0)
    assert metodos["Dinheiro"] == pytest.approx(80.0)


def test_parcial_nao_conta_como_fechada(c):
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

    hoje = datetime.date.today().isoformat()

    # Não aparece em vendas do dia
    resp = c.get("/api/relatorios/vendas-do-dia")
    assert resp.status_code == 200
    ids = [cmd["id"] for cmd in resp.json()["comandas"]]
    assert cid not in ids

    # Não aparece em fechamento de caixa
    resp = c.get(f"/api/relatorios/fechamento-caixa?data={hoje}")
    assert resp.status_code == 200
    ids = [cmd["id"] for cmd in resp.json().get("comandas", [])]
    assert cid not in ids

    # Não aparece em histórico
    resp = c.get(f"/api/relatorios/historico-comandas?data_inicio={hoje}&data_fim={hoje}")
    assert resp.status_code == 200
    ids = [cmd["id"] for cmd in resp.json()["comandas"]]
    assert cid not in ids
