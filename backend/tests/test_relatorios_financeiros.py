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
    resp = c.post(
        "/api/itens",
        json={"nome": nome, "tipo": "simples", "vendavel": True, "unidade_base": "un", "preco_venda": preco},
    )
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


def _set_custo_medio(item_id: int, custo: Decimal) -> None:
    from src.models.itens import Item
    db: Session = _TestingSession()
    try:
        db.execute(update(Item).where(Item.id == item_id).values(custo_medio=custo))
        db.commit()
    finally:
        db.close()


def _baixa_sem_venda(c, item_id, quantidade, motivo):
    resp = c.post(
        "/api/estoque/baixa-sem-venda",
        json={"item_id": item_id, "quantidade": str(quantidade), "motivo": motivo},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _mes_atual() -> str:
    hoje = datetime.date.today()
    return f"{hoje.year}-{hoje.month:02d}"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_dre_produto_sem_custo_gera_alerta(c):
    """Item vendido sem custo_medio → DRE retorna lista produtos_sem_custo com o item."""
    garcom = _criar_garcom(c)
    item = _criar_item(c, nome="SemCusto", preco="30.00")
    metodo = _criar_metodo(c)
    # item.custo_medio = None (default, não setamos custo)

    comanda = _abrir_comanda(c, garcom["id"])
    _lancar_item(c, comanda["id"], item["id"], comanda["version"])
    _fechar(c, comanda["id"], metodo["id"], "30.00")

    resp = c.get(f"/api/relatorios/dre?mes={_mes_atual()}")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    nomes_sem_custo = [p["nome"] for p in data["produtos_sem_custo"]]
    assert "SemCusto" in nomes_sem_custo
    assert float(data["cmv"]) == pytest.approx(0.0)


def test_dre_cortesia_entra_cmv_nao_receita(c):
    """Cortesia: CMV inclui custo do item cortesia; faturamento_liquido não inclui."""
    garcom = _criar_garcom(c)
    item = _criar_item(c, nome="Bebida", preco="20.00")
    _set_custo_medio(item["id"], Decimal("8.00"))
    metodo = _criar_metodo(c)

    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]
    # 1 item normal
    resp1 = _lancar_item(c, cid, item["id"], comanda["version"])
    # 1 item cortesia
    _lancar_item(c, cid, item["id"], resp1["version"], cortesia=True)
    # total: apenas o item normal = 20.00
    _fechar(c, cid, metodo["id"], "20.00")

    resp = c.get(f"/api/relatorios/dre?mes={_mes_atual()}")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # faturamento_liquido = caixa recebido = 20.00
    assert float(data["faturamento_liquido"]) == pytest.approx(20.0)
    # cmv = 8 (normal) + 8 (cortesia) = 16
    assert float(data["cmv"]) == pytest.approx(16.0)
    # cortesias_valor = preco_venda da cortesia = 20.00
    assert float(data["cortesias_valor"]) == pytest.approx(20.0)


def test_cmv_classificacao_faixas(c):
    """Itens com margens 50%, 30%, 10% recebem verde, amarelo, vermelho."""
    # verde: preco=10, custo=5 → margem=50%
    i1 = _criar_item(c, nome="Verde", preco="10.00")
    _set_custo_medio(i1["id"], Decimal("5.00"))
    # amarelo: preco=10, custo=7 → margem=30%
    i2 = _criar_item(c, nome="Amarelo", preco="10.00")
    _set_custo_medio(i2["id"], Decimal("7.00"))
    # vermelho: preco=10, custo=9 → margem=10%
    i3 = _criar_item(c, nome="Vermelho", preco="10.00")
    _set_custo_medio(i3["id"], Decimal("9.00"))

    resp = c.get("/api/relatorios/cmv-por-produto")
    assert resp.status_code == 200, resp.text
    itens = {i["nome"]: i["classificacao"] for i in resp.json()["itens"]}

    assert itens["Verde"] == "verde"
    assert itens["Amarelo"] == "amarelo"
    assert itens["Vermelho"] == "vermelho"


def test_perdas_agrupadas_por_motivo(c):
    """2 baixas sem venda com motivos distintos → 2 grupos separados com totais."""
    item = _criar_item(c, nome="Insumo", preco="5.00")
    _set_custo_medio(item["id"], Decimal("3.00"))

    _baixa_sem_venda(c, item["id"], "2", "perda")
    _baixa_sem_venda(c, item["id"], "1", "quebra")

    hoje = datetime.date.today().isoformat()
    resp = c.get(f"/api/relatorios/perdas-cortesias?data_inicio={hoje}&data_fim={hoje}")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    motivos = {g["motivo"]: g for g in data["grupos"]}
    assert "perda" in motivos
    assert "quebra" in motivos
    assert float(motivos["perda"]["total_valor"]) == pytest.approx(6.0)  # 2 * 3.00
    assert float(motivos["quebra"]["total_valor"]) == pytest.approx(3.0)  # 1 * 3.00
    assert float(data["total_geral"]) == pytest.approx(9.0)


def test_vendas_por_garcom_respeita_garcom_abertura(c):
    """Cada garçom vê apenas suas próprias comandas (garçom da abertura)."""
    g1 = _criar_garcom(c, "Ana")
    g2 = _criar_garcom(c, "Bruno")
    item = _criar_item(c, preco="40.00")
    metodo = _criar_metodo(c)

    cmd1 = _abrir_comanda(c, g1["id"], "Mesa 1")
    _lancar_item(c, cmd1["id"], item["id"], cmd1["version"])
    _fechar(c, cmd1["id"], metodo["id"], "40.00")

    cmd2 = _abrir_comanda(c, g2["id"], "Mesa 2")
    _lancar_item(c, cmd2["id"], item["id"], cmd2["version"])
    _fechar(c, cmd2["id"], metodo["id"], "40.00")

    hoje = datetime.date.today().isoformat()
    resp = c.get(f"/api/relatorios/vendas-por-garcom?data_inicio={hoje}&data_fim={hoje}")
    assert resp.status_code == 200, resp.text
    garcons = {g["garcom_nome"]: g for g in resp.json()["garcons"]}

    assert "Ana" in garcons
    assert "Bruno" in garcons
    assert garcons["Ana"]["qtd_comandas"] == 1
    assert garcons["Bruno"]["qtd_comandas"] == 1
    assert float(garcons["Ana"]["faturamento"]) == pytest.approx(40.0)
    assert float(garcons["Bruno"]["faturamento"]) == pytest.approx(40.0)
