import os
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_current_user, get_db
from src.core.database import Base
from src.main import app

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSession = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def _fake_user() -> dict:
    return {
        "sub": "1",
        "user_id": 1,
        "tenant_id": 1,
        "permissions": ["caixa"],
    }


def _fake_user_sem_caixa() -> dict:
    return {
        "sub": "2",
        "user_id": 2,
        "tenant_id": 1,
        "permissions": ["comandas"],
    }


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


@pytest.fixture
def client():
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


@pytest.fixture
def client_sem_permissao():
    def override_get_db():
        db = _TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _fake_user_sem_caixa
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Abrir caixa
# ---------------------------------------------------------------------------

def test_abrir_caixa(client):
    r = client.post("/api/caixa/abrir", json={"valor_abertura": "100.00"})
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["status"] == "aberta"
    assert Decimal(data["valor_abertura"]) == Decimal("100.00")
    assert data["movimentos"] == []


def test_abrir_caixa_dupla_retorna_409(client):
    client.post("/api/caixa/abrir", json={"valor_abertura": "50.00"})
    r = client.post("/api/caixa/abrir", json={"valor_abertura": "80.00"})
    assert r.status_code == 409, r.text


def test_abrir_sem_permissao_retorna_403(client_sem_permissao):
    r = client_sem_permissao.post("/api/caixa/abrir", json={"valor_abertura": "50.00"})
    assert r.status_code == 403, r.text


# ---------------------------------------------------------------------------
# GET sessão
# ---------------------------------------------------------------------------

def test_get_sessao_sem_abrir_retorna_404(client):
    r = client.get("/api/caixa/sessao")
    assert r.status_code == 404, r.text


def test_get_sessao_retorna_aberta(client):
    client.post("/api/caixa/abrir", json={"valor_abertura": "200.00"})
    r = client.get("/api/caixa/sessao")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "aberta"


# ---------------------------------------------------------------------------
# Movimentos
# ---------------------------------------------------------------------------

def test_registrar_suprimento(client):
    client.post("/api/caixa/abrir", json={"valor_abertura": "100.00"})
    r = client.post(
        "/api/caixa/movimentos",
        json={"tipo": "suprimento", "valor": "50.00", "motivo": "Troco extra"},
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["tipo"] == "suprimento"
    assert Decimal(data["valor"]) == Decimal("50.00")


def test_registrar_sangria(client):
    client.post("/api/caixa/abrir", json={"valor_abertura": "300.00"})
    r = client.post(
        "/api/caixa/movimentos",
        json={"tipo": "sangria", "valor": "100.00", "motivo": "Retirada gerente"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["tipo"] == "sangria"


def test_movimento_sem_sessao_retorna_404(client):
    r = client.post(
        "/api/caixa/movimentos",
        json={"tipo": "sangria", "valor": "10.00", "motivo": "teste"},
    )
    assert r.status_code == 404, r.text


# ---------------------------------------------------------------------------
# Fechar caixa
# ---------------------------------------------------------------------------

def test_fechar_caixa_calcula_diferenca(client):
    client.post("/api/caixa/abrir", json={"valor_abertura": "100.00"})
    # suprimento +50, sangria -30 → valor_esperado = 100 + 0 (dinheiro) + 50 - 30 = 120
    client.post("/api/caixa/movimentos", json={"tipo": "suprimento", "valor": "50.00", "motivo": "aporte"})
    client.post("/api/caixa/movimentos", json={"tipo": "sangria", "valor": "30.00", "motivo": "retirada"})
    r = client.post("/api/caixa/fechar", json={"valor_informado": "115.00"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "fechada"
    assert Decimal(data["valor_esperado"]) == Decimal("120.00")
    assert Decimal(data["valor_informado"]) == Decimal("115.00")
    assert Decimal(data["diferenca"]) == Decimal("-5.00")


def test_fechar_sem_sessao_retorna_404(client):
    r = client.post("/api/caixa/fechar", json={"valor_informado": "100.00"})
    assert r.status_code == 404, r.text


def test_fechar_inclui_movimentos_na_resposta(client):
    client.post("/api/caixa/abrir", json={"valor_abertura": "200.00"})
    client.post("/api/caixa/movimentos", json={"tipo": "sangria", "valor": "20.00", "motivo": "x"})
    r = client.post("/api/caixa/fechar", json={"valor_informado": "180.00"})
    assert r.status_code == 200, r.text
    assert len(r.json()["movimentos"]) == 1


def test_sessao_fecha_impede_nova_abertura_ate_fechar(client):
    # open → register mov → close → reopen should succeed (no duplicate open)
    client.post("/api/caixa/abrir", json={"valor_abertura": "50.00"})
    client.post("/api/caixa/fechar", json={"valor_informado": "50.00"})
    r = client.post("/api/caixa/abrir", json={"valor_abertura": "60.00"})
    assert r.status_code == 201, r.text
