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


def _inserir_estabelecimento(c_fixture):
    db: Session = _TestingSession()
    try:
        from src.models.estabelecimento import Estabelecimento
        estab = Estabelecimento(id=1, nome="Bar Teste", cnpj="12.345.678/0001-99", endereco="Rua A, 1", telefone="(11) 9999-9999")
        db.add(estab)
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_comprovante_comanda_fechada(c):
    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="30.00")
    metodo = _criar_metodo(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]
    version = comanda["version"]

    _lancar_item(c, cid, item["id"], version)
    _fechar(c, cid, metodo["id"], "30.00")

    resp = c.get(f"/api/comandas/{cid}/comprovante")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["comanda_id"] == cid
    assert len(data["itens"]) == 1
    assert float(data["itens"][0]["subtotal"]) == 30.0
    assert len(data["pagamentos"]) == 1
    assert float(data["pagamentos"][0]["valor"]) == 30.0
    assert float(data["total"]) == 30.0


def test_comprovante_sem_estabelecimento_usa_fallback(c):
    garcom = _criar_garcom(c)
    item = _criar_item(c)
    metodo = _criar_metodo(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]
    version = comanda["version"]
    _lancar_item(c, cid, item["id"], version)
    _fechar(c, cid, metodo["id"], "50.00")

    resp = c.get(f"/api/comandas/{cid}/comprovante")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["estabelecimento"]["nome"] == "Estabelecimento"
    assert data["estabelecimento"]["cnpj"] is None


def test_comprovante_com_estabelecimento(c):
    _inserir_estabelecimento(c)
    garcom = _criar_garcom(c)
    item = _criar_item(c)
    metodo = _criar_metodo(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]
    version = comanda["version"]
    _lancar_item(c, cid, item["id"], version)
    _fechar(c, cid, metodo["id"], "50.00")

    resp = c.get(f"/api/comandas/{cid}/comprovante")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["estabelecimento"]["nome"] == "Bar Teste"
    assert data["estabelecimento"]["cnpj"] == "12.345.678/0001-99"


def test_comprovante_comanda_inexistente_retorna_404(c):
    resp = c.get("/api/comandas/99999/comprovante")
    assert resp.status_code == 404, resp.text
