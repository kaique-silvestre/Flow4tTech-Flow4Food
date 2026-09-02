import os

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
from src.models.audit_logs import AuditLog
from src.models.insumos import Insumo
from src.services import audit_service

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


def _log_background_sync(action, *, tenant_id=None, user_id=None, entity=None, entity_id=None, before=None, after=None, impersonated_by=None):
    db = _TestingSession()
    try:
        audit_service.log(
            db,
            action,
            tenant_id=tenant_id,
            user_id=user_id,
            entity=entity,
            entity_id=entity_id,
            before=before,
            after=after,
            impersonated_by=impersonated_by,
        )
    finally:
        db.close()


@pytest.fixture
def crud_client(monkeypatch):
    def override_get_db():
        db = _TestingSession()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(audit_service, "log_background", _log_background_sync)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _fake_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _criar_item(c, nome="Item A", tipo="simples", vendavel=False):
    payload = {"nome": nome, "unidade_base": "un"}
    resp = c.post("/api/insumos", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _comprar(c, item_id, quantidade, custo_total, data="2026-05-07"):
    payload = {
        "data_compra": data,
        "itens": [{"item_id": item_id, "quantidade": quantidade, "custo_total": custo_total}],
    }
    resp = c.post("/api/compras", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _get_item(c, item_id):
    resp = c.get(f"/api/insumos/{item_id}")
    assert resp.status_code == 200
    return resp.json()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_criar_compra_simples(crud_client):
    item = _criar_item(crud_client, "Coca Lata")
    compra = _comprar(crud_client, item["id"], 100, 200.0)

    assert float(compra["total"]) == pytest.approx(200.0)
    assert len(compra["itens"]) == 1
    assert compra["itens"][0]["item_nome"] == "Coca Lata"
    assert float(compra["itens"][0]["custo_unitario"]) == pytest.approx(2.0)

    atualizado = _get_item(crud_client, item["id"])
    assert float(atualizado["estoque_atual"]) == pytest.approx(100.0)
    assert float(atualizado["custo_medio"]) == pytest.approx(2.0)


def test_custo_medio_ponderado(crud_client):
    item = _criar_item(crud_client, "Produto X")
    # Compra 1: 100 un a R$2,00/un → custo_medio = 2.00
    _comprar(crud_client, item["id"], 100, 200.0)
    # Compra 2: 100 un a R$4,00/un → custo_medio = (100*2 + 100*4)/(200) = 3.00
    _comprar(crud_client, item["id"], 100, 400.0)

    atualizado = _get_item(crud_client, item["id"])
    assert float(atualizado["estoque_atual"]) == pytest.approx(200.0)
    assert float(atualizado["custo_medio"]) == pytest.approx(3.0)


def test_reset_custo_estoque_zero(crud_client):
    item = _criar_item(crud_client, "Produto Y")
    # Estoque = 0 (inicial) → reset: custo_medio = custo_unitario da compra
    _comprar(crud_client, item["id"], 50, 150.0)  # custo_unitario = 3.00

    atualizado = _get_item(crud_client, item["id"])
    assert float(atualizado["custo_medio"]) == pytest.approx(3.0)


def test_reset_custo_estoque_negativo(crud_client):
    item = _criar_item(crud_client, "Produto Z")
    # Força estoque negativo via baixa sem venda
    crud_client.post("/api/estoque/baixa-sem-venda", json={
        "item_id": item["id"], "quantidade": 10, "motivo": "perda"
    })
    # Estoque = -10 → compra deve resetar custo_medio para o novo custo
    _comprar(crud_client, item["id"], 100, 500.0)  # custo_unitario = 5.00

    atualizado = _get_item(crud_client, item["id"])
    assert float(atualizado["custo_medio"]) == pytest.approx(5.0)


def test_criar_compra_gera_movimento(crud_client):
    item = _criar_item(crud_client, "Item Mov")
    _comprar(crud_client, item["id"], 10, 50.0)

    resp = crud_client.get("/api/estoque/movimentos")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["itens"][0]["tipo"] == "entrada"
    assert data["itens"][0]["item_nome"] == "Item Mov"
    assert float(data["itens"][0]["quantidade"]) == pytest.approx(10.0)


def test_filtro_periodo_compras(crud_client):
    item = _criar_item(crud_client, "Item Filtro")
    _comprar(crud_client, item["id"], 10, 20.0, data="2026-01-01")
    _comprar(crud_client, item["id"], 5, 15.0, data="2026-03-01")

    resp = crud_client.get("/api/compras?data_inicio=2026-02-01&data_fim=2026-04-01")
    assert resp.status_code == 200
    itens = resp.json()["itens"]
    assert len(itens) == 1
    assert itens[0]["data_compra"] == "2026-03-01"


def test_compra_item_inexistente(crud_client):
    payload = {
        "data_compra": "2026-05-07",
        "itens": [{"item_id": 9999, "quantidade": 1, "custo_total": 10.0}],
    }
    resp = crud_client.post("/api/compras", json=payload)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Auditoria
# ---------------------------------------------------------------------------

def test_criar_compra_gera_log_de_auditoria(crud_client):
    item = _criar_item(crud_client, "Item Auditado")
    compra = _comprar(crud_client, item["id"], 10, 20.0)

    db = _TestingSession()
    logs = db.query(AuditLog).filter_by(action="compra.criar").all()
    db.close()

    assert len(logs) == 1
    log = logs[0]
    assert log.user_id == _fake_user()["user_id"]
    assert log.entity == "Compra"
    assert log.entity_id == compra["id"]


def test_confirmar_recebimento_gera_log_de_auditoria(crud_client):
    item = _criar_item(crud_client, "Item Agendado")
    payload = {
        "data_compra": "2026-05-07",
        "tipo_compra": "agendada",
        "data_prevista_recebimento": "2026-05-10",
        "data_prevista_pagamento": "2026-05-20",
        "itens": [{"item_id": item["id"], "quantidade": 5, "custo_total": 50.0}],
    }
    resp = crud_client.post("/api/compras", json=payload)
    assert resp.status_code == 201, resp.text
    compra_id = resp.json()["id"]

    resp = crud_client.post(f"/api/compras/{compra_id}/confirmar-recebimento")
    assert resp.status_code == 200, resp.text

    db = _TestingSession()
    logs = db.query(AuditLog).filter_by(action="compra.confirmar_recebimento").all()
    db.close()

    assert len(logs) == 1
    assert logs[0].entity == "Compra"
    assert logs[0].entity_id == compra_id


def test_cancelar_compra_gera_log_de_auditoria(crud_client):
    item = _criar_item(crud_client, "Item Cancelado")
    compra = _comprar(crud_client, item["id"], 10, 20.0)

    resp = crud_client.post(f"/api/compras/{compra['id']}/cancelar")
    assert resp.status_code == 200, resp.text

    db = _TestingSession()
    logs = db.query(AuditLog).filter_by(action="compra.cancelar").all()
    db.close()

    assert len(logs) == 1
    assert logs[0].entity == "Compra"
    assert logs[0].entity_id == compra["id"]


# ---------------------------------------------------------------------------
# Descarte de item com insumo removido (não deve ser silencioso)
# ---------------------------------------------------------------------------

def test_confirmar_recebimento_loga_warning_quando_insumo_removido(crud_client, caplog):
    item = _criar_item(crud_client, "Item Sumiu")
    payload = {
        "data_compra": "2026-05-07",
        "tipo_compra": "agendada",
        "data_prevista_recebimento": "2026-05-10",
        "data_prevista_pagamento": "2026-05-20",
        "itens": [{"item_id": item["id"], "quantidade": 5, "custo_total": 50.0}],
    }
    resp = crud_client.post("/api/compras", json=payload)
    assert resp.status_code == 201, resp.text
    compra_id = resp.json()["id"]

    db = _TestingSession()
    db.query(Insumo).filter_by(id=item["id"]).delete()
    db.commit()
    db.close()

    with caplog.at_level("WARNING"):
        resp = crud_client.post(f"/api/compras/{compra_id}/confirmar-recebimento")
    assert resp.status_code == 200, resp.text

    assert any(
        rec.levelname == "WARNING" and "compra_item_insumo_ausente" in rec.message
        for rec in caplog.records
    )


def test_cancelar_compra_loga_warning_quando_insumo_removido(crud_client, caplog):
    item = _criar_item(crud_client, "Item Sumiu 2")
    compra = _comprar(crud_client, item["id"], 10, 20.0)

    db = _TestingSession()
    db.query(Insumo).filter_by(id=item["id"]).delete()
    db.commit()
    db.close()

    with caplog.at_level("WARNING"):
        resp = crud_client.post(f"/api/compras/{compra['id']}/cancelar")
    assert resp.status_code == 200, resp.text

    assert any(
        rec.levelname == "WARNING" and "compra_item_insumo_ausente" in rec.message
        for rec in caplog.records
    )
