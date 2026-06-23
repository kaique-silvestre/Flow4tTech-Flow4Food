import datetime
import os
from decimal import Decimal
from unittest.mock import patch

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
from src.models.garcons import Garcom
from src.models.produtos import Produto
from src.models.promocoes import Promocao, PromocaoProduto

_SQLITE_URL = "sqlite:///:memory:"
_engine = create_engine(
    _SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSession = sessionmaker(bind=_engine, autoflush=False, autocommit=False)

_TODAY = datetime.date(2026, 6, 11)  # Wednesday; Python weekday=2; spec weekday=3 (Qua)
_NOW = datetime.datetime(2026, 6, 11, 12, 0, 0)


def _fake_user():
    return {
        "sub": "1",
        "user_id": 1,
        "tenant_id": 1,
        "permissions": ["cadastros", "comandas", "compras", "configuracoes", "dashboard", "estoque", "gestao_usuarios", "relatorios"],
    }


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


@pytest.fixture
def db():
    session = _TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def crud_client():
    def override_get_db():
        s = _TestingSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _fake_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_garcom(db) -> int:
    g = Garcom(nome="Joao", ativo=True)
    db.add(g)
    db.commit()
    db.refresh(g)
    return g.id


def _seed_produto(db, preco="10.00") -> int:
    p = Produto(nome="Coca", preco_venda=Decimal(preco), ativo=True)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p.id


def _seed_promo(db, produto_id, tipo="porcentagem", valor="10.00",
                hora_inicio=datetime.time(0, 0), hora_fim=datetime.time(23, 59, 59),
                recorrencia="nenhuma", dias_semana=None, dias_mes=None,
                data_inicio=None, data_fim=None) -> Promocao:
    promo = Promocao(
        nome="Promo Teste",
        tipo_desconto=tipo,
        valor_desconto=Decimal(valor),
        data_inicio=data_inicio or _TODAY,
        data_fim=data_fim,
        hora_inicio=hora_inicio,
        hora_fim=hora_fim,
        recorrencia=recorrencia,
        dias_semana=dias_semana,
        dias_mes=dias_mes,
        created_at=_NOW,
    )
    db.add(promo)
    db.flush()
    pp = PromocaoProduto(promocao_id=promo.id, produto_id=produto_id)
    db.add(pp)
    db.commit()
    db.refresh(promo)
    return promo


def _abrir_comanda(c, garcom_id):
    r = c.post("/api/comandas", json={
        "identificacao": "Mesa 1",
        "tipo_identificacao": "mesa",
        "garcom_id": garcom_id,
        "pessoas": ["A"],
    })
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# F1 — porcentagem desconto aplicado
# ---------------------------------------------------------------------------

def test_f1_promo_porcentagem(crud_client, db):
    garcom_id = _seed_garcom(db)
    produto_id = _seed_produto(db, "10.00")
    _seed_promo(db, produto_id, tipo="porcentagem", valor="10.00")

    comanda = _abrir_comanda(crud_client, garcom_id)

    with patch("src.services.comandas_service.datetime") as mock_dt:
        mock_dt.date.today.return_value = _TODAY
        mock_dt.datetime.now.return_value = _NOW
        r = crud_client.post(
            f"/api/comandas/{comanda['id']}/itens",
            json={"item_id": produto_id, "quantidade": "1", "version": comanda["version"]},
        )

    assert r.status_code == 200, r.text
    item = r.json()["itens_ativos"][0]
    assert Decimal(item["preco_unitario"]) == Decimal("9.00")
    assert item["promocao_id"] is not None


# ---------------------------------------------------------------------------
# F2 — valor_fixo desconto aplicado
# ---------------------------------------------------------------------------

def test_f2_promo_valor_fixo(crud_client, db):
    garcom_id = _seed_garcom(db)
    produto_id = _seed_produto(db, "10.00")
    _seed_promo(db, produto_id, tipo="valor_fixo", valor="3.00")

    comanda = _abrir_comanda(crud_client, garcom_id)

    with patch("src.services.comandas_service.datetime") as mock_dt:
        mock_dt.date.today.return_value = _TODAY
        mock_dt.datetime.now.return_value = _NOW
        r = crud_client.post(
            f"/api/comandas/{comanda['id']}/itens",
            json={"item_id": produto_id, "quantidade": "1", "version": comanda["version"]},
        )

    assert r.status_code == 200, r.text
    item = r.json()["itens_ativos"][0]
    assert Decimal(item["preco_unitario"]) == Decimal("7.00")


# ---------------------------------------------------------------------------
# F3 — fora da janela de horário → sem desconto
# ---------------------------------------------------------------------------

def test_f3_fora_janela_horario(crud_client, db):
    garcom_id = _seed_garcom(db)
    produto_id = _seed_produto(db, "10.00")
    _seed_promo(
        db, produto_id, tipo="porcentagem", valor="10.00",
        hora_inicio=datetime.time(8, 0), hora_fim=datetime.time(10, 0),
    )

    comanda = _abrir_comanda(crud_client, garcom_id)

    # hora_agora = 12:00, fora da janela 08:00–10:00
    with patch("src.services.comandas_service.datetime") as mock_dt:
        mock_dt.date.today.return_value = _TODAY
        mock_dt.datetime.now.return_value = _NOW
        r = crud_client.post(
            f"/api/comandas/{comanda['id']}/itens",
            json={"item_id": produto_id, "quantidade": "1", "version": comanda["version"]},
        )

    assert r.status_code == 200, r.text
    item = r.json()["itens_ativos"][0]
    assert Decimal(item["preco_unitario"]) == Decimal("10.00")
    assert item["promocao_id"] is None


# ---------------------------------------------------------------------------
# F4 — cortesia → sem desconto
# ---------------------------------------------------------------------------

def test_f4_cortesia_sem_desconto(crud_client, db):
    garcom_id = _seed_garcom(db)
    produto_id = _seed_produto(db, "10.00")
    _seed_promo(db, produto_id, tipo="porcentagem", valor="50.00")

    comanda = _abrir_comanda(crud_client, garcom_id)

    with patch("src.services.comandas_service.datetime") as mock_dt:
        mock_dt.date.today.return_value = _TODAY
        mock_dt.datetime.now.return_value = _NOW
        r = crud_client.post(
            f"/api/comandas/{comanda['id']}/itens",
            json={"item_id": produto_id, "quantidade": "1", "cortesia": True, "version": comanda["version"]},
        )

    assert r.status_code == 200, r.text
    item = r.json()["itens_ativos"][0]
    assert Decimal(item["preco_unitario"]) == Decimal("0.00")
    assert item["promocao_id"] is None


# ---------------------------------------------------------------------------
# F5 — conflito: duas promos ativas → menor id
# ---------------------------------------------------------------------------

def test_f5_conflito_menor_id(crud_client, db):
    garcom_id = _seed_garcom(db)
    produto_id = _seed_produto(db, "10.00")
    promo1 = _seed_promo(db, produto_id, tipo="porcentagem", valor="10.00")
    promo2 = _seed_promo(db, produto_id, tipo="porcentagem", valor="20.00")
    assert promo1.id < promo2.id

    comanda = _abrir_comanda(crud_client, garcom_id)

    with patch("src.services.comandas_service.datetime") as mock_dt:
        mock_dt.date.today.return_value = _TODAY
        mock_dt.datetime.now.return_value = _NOW
        r = crud_client.post(
            f"/api/comandas/{comanda['id']}/itens",
            json={"item_id": produto_id, "quantidade": "1", "version": comanda["version"]},
        )

    assert r.status_code == 200, r.text
    item = r.json()["itens_ativos"][0]
    assert Decimal(item["preco_unitario"]) == Decimal("9.00")
    assert item["promocao_id"] == promo1.id


# ---------------------------------------------------------------------------
# F6 — recorrência semanal: dia errado → sem desconto
# ---------------------------------------------------------------------------

def test_f6_recorrencia_semanal_dia_errado(crud_client, db):
    garcom_id = _seed_garcom(db)
    produto_id = _seed_produto(db, "10.00")
    # _TODAY is Wednesday → spec weekday=3; pass [1,2] (Mon,Tue) → no match
    _seed_promo(db, produto_id, tipo="porcentagem", valor="20.00",
                recorrencia="semanal", dias_semana=[1, 2])

    comanda = _abrir_comanda(crud_client, garcom_id)

    with patch("src.services.comandas_service.datetime") as mock_dt:
        mock_dt.date.today.return_value = _TODAY
        mock_dt.datetime.now.return_value = _NOW
        r = crud_client.post(
            f"/api/comandas/{comanda['id']}/itens",
            json={"item_id": produto_id, "quantidade": "1", "version": comanda["version"]},
        )

    assert r.status_code == 200, r.text
    item = r.json()["itens_ativos"][0]
    assert Decimal(item["preco_unitario"]) == Decimal("10.00")
    assert item["promocao_id"] is None
