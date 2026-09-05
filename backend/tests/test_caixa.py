import os
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_current_user, get_db
from src.core.database import Base
from src.core.errors import AppError, ErrorCode
from src.main import app
from src.repositories import caixa_repository
from src.schemas.caixa import FecharCaixaRequest
from src.schemas.contas_pagar_schemas import PagarContaRequest
from src.services import caixa_service, contas_pagar_service

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


def test_fechar_caixa_com_divergencia_emite_warning_estruturado(client, monkeypatch):
    class _Logger:
        def __init__(self):
            self.calls: list[tuple[str, dict]] = []

        def info(self, _event: str, **_kwargs):
            pass

        def warning(self, event: str, **kwargs):
            self.calls.append((event, kwargs))

    logger = _Logger()
    monkeypatch.setattr(caixa_service, "logger", logger)
    client.post("/api/caixa/abrir", json={"valor_abertura": "100.00"})

    response = client.post("/api/caixa/fechar", json={"valor_informado": "95.00"})

    assert response.status_code == 200, response.text
    assert logger.calls == [
        (
            "caixa_fechado_com_divergencia",
            {
                "sessao_id": response.json()["id"],
                "user_id": 1,
                "valor_informado": "95.00",
                "valor_esperado": "100.00",
                "diferenca": "-5.00",
            },
        )
    ]


@pytest.mark.parametrize(
    "body",
    [
        {"valor_abertura": "100000000.00"},
        {"valor_abertura": "10.001"},
    ],
)
def test_abrir_caixa_rejeita_valor_fora_da_precisao_monetaria(client, body):
    response = client.post("/api/caixa/abrir", json=body)

    assert response.status_code == 422, response.text


def test_pagamento_em_dinheiro_registra_sangria_pela_camada_caixa(monkeypatch):
    conta = SimpleNamespace(
        id=42,
        status="pendente",
        data_pagamento=None,
        metodo_pagamento_id=None,
        observacao=None,
        valor=Decimal("25.00"),
    )
    metodo = SimpleNamespace(tipo="dinheiro", ativo=True)

    class _Db:
        def execute(self, _statement):
            return SimpleNamespace(scalar_one_or_none=lambda: metodo)

        def flush(self):
            pass

        def commit(self):
            pass

        def rollback(self):
            pass

        def refresh(self, _obj):
            pass

    calls: list[tuple] = []
    monkeypatch.setattr(
        contas_pagar_service.contas_pagar_repository, "get_by_id", lambda *_: conta
    )
    monkeypatch.setattr(contas_pagar_service, "_to_response", lambda *_: conta)
    monkeypatch.setattr(
        caixa_service,
        "registrar_movimento",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    result = contas_pagar_service.pagar_conta(
        _Db(),
        conta.id,
        PagarContaRequest(data_pagamento=date.today(), metodo_pagamento_id=1),
        user_id=7,
    )

    assert result is conta
    assert len(calls) == 1
    args, kwargs = calls[0]
    _, movimento, user_id = args
    assert movimento.tipo == "sangria"
    assert movimento.valor == Decimal("25.00")
    assert movimento.motivo == "Pagamento de conta a pagar #42"
    assert user_id == 7
    assert kwargs == {"commit": False}


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


# ---------------------------------------------------------------------------
# Fechamento concorrente
# ---------------------------------------------------------------------------

def test_fechamento_concorrente_um_sucede_outro_recebe_conflito(client):
    client.post("/api/caixa/abrir", json={"valor_abertura": "100.00"})

    db_a = _TestingSession()
    db_b = _TestingSession()
    try:
        # Both "requests" read the session while it is still open, before
        # either has written its close back.
        sessao_a = caixa_repository.get_sessao_aberta(db_a)
        sessao_b = caixa_repository.get_sessao_aberta(db_b)
        assert sessao_a is not None and sessao_b is not None

        resultado_a = caixa_repository.fechar_sessao(
            db_a,
            sessao_id=sessao_a.id,
            valor_informado=Decimal("100.00"),
            valor_esperado=Decimal("100.00"),
            user_id=1,
        )
        db_a.commit()
        assert resultado_a is not None
        assert resultado_a.status == "fechada"

        resultado_b = caixa_repository.fechar_sessao(
            db_b,
            sessao_id=sessao_b.id,
            valor_informado=Decimal("90.00"),
            valor_esperado=Decimal("100.00"),
            user_id=2,
        )
        db_b.commit()
        assert resultado_b is None
    finally:
        db_a.close()
        db_b.close()


def test_fechar_caixa_service_levanta_conflito_quando_ja_fechado(client, monkeypatch):
    client.post("/api/caixa/abrir", json={"valor_abertura": "100.00"})

    db = _TestingSession()
    try:
        # Simulate a request that read the session as open, but loses the
        # race: by the time it tries to write, the session is already
        # closed (fechar_sessao's CAS update matches 0 rows).
        monkeypatch.setattr(caixa_repository, "fechar_sessao", lambda *a, **k: None)
        with pytest.raises(AppError) as exc_info:
            caixa_service.fechar_caixa(
                db, FecharCaixaRequest(valor_informado=Decimal("100.00")), user_id=1
            )
        assert exc_info.value.code == ErrorCode.CAIXA_JA_FECHADO
        assert exc_info.value.http_status == 409
    finally:
        db.close()
