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
from src.models.movimentos_estoque import MovimentoEstoque
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


def _comprar(c, item_id, quantidade, custo_total):
    payload = {
        "data_compra": "2026-05-07",
        "itens": [{"item_id": item_id, "quantidade": quantidade, "custo_total": custo_total}],
    }
    resp = c.post("/api/compras", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _baixa(c, item_id, quantidade, motivo="perda", observacao=None):
    payload = {"item_id": item_id, "quantidade": quantidade, "motivo": motivo}
    if observacao:
        payload["observacao"] = observacao
    return c.post("/api/estoque/baixa-sem-venda", json=payload)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_baixa_sem_venda_atualiza_saldo(crud_client):
    item = _criar_item(crud_client, "Coca Lata")
    _comprar(crud_client, item["id"], 100, 200.0)

    resp = _baixa(crud_client, item["id"], 10, "perda")
    assert resp.status_code == 201
    data = resp.json()
    assert data["saldo_negativo"] is False
    assert float(data["movimento"]["saldo_apos"]) == pytest.approx(90.0)
    assert data["movimento"]["tipo"] == "saida_perda"
    assert data["movimento"]["motivo"] == "perda"

    saldo = crud_client.get("/api/estoque/saldo").json()["itens"]
    item_saldo = next(s for s in saldo if s["id"] == item["id"])
    assert float(item_saldo["estoque_atual"]) == pytest.approx(90.0)


def test_baixa_saldo_negativo_permitido(crud_client):
    item = _criar_item(crud_client, "Item Neg")

    resp = _baixa(crud_client, item["id"], 5, "outro")
    assert resp.status_code == 201
    data = resp.json()
    assert data["saldo_negativo"] is True
    assert float(data["movimento"]["saldo_apos"]) == pytest.approx(-5.0)


def test_baixa_produto_nao_encontrado(crud_client):
    resp = crud_client.post("/api/produtos", json={"nome": "Produto Y", "preco_venda": 10.0})
    assert resp.status_code == 201
    produto = resp.json()

    resp = _baixa(crud_client, produto["id"], 1)
    assert resp.status_code == 404


def test_historico_ordenado_desc(crud_client):
    item = _criar_item(crud_client, "Item Hist")
    _comprar(crud_client, item["id"], 50, 100.0)
    _baixa(crud_client, item["id"], 5, "cortesia")

    resp = crud_client.get("/api/estoque/movimentos")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    # Mais recente primeiro (saida_perda > entrada)
    assert data["itens"][0]["tipo"] == "saida_perda"
    assert data["itens"][1]["tipo"] == "entrada"


def test_historico_filtro_tipo(crud_client):
    item = _criar_item(crud_client, "Item Tipo")
    _comprar(crud_client, item["id"], 50, 100.0)
    _baixa(crud_client, item["id"], 5, "quebra")

    resp = crud_client.get("/api/estoque/movimentos?tipo=entrada")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["itens"][0]["tipo"] == "entrada"


def test_saldo_exclui_produtos(crud_client):
    _criar_item(crud_client, "Insumo Saldo")
    crud_client.post("/api/produtos", json={"nome": "Produto Saldo", "preco_venda": 15.0})

    resp = crud_client.get("/api/estoque/saldo")
    assert resp.status_code == 200
    nomes = [s["nome"] for s in resp.json()["itens"]]
    assert "Insumo Saldo" in nomes
    assert "Produto Saldo" not in nomes


def test_saldo_filtro_busca(crud_client):
    _criar_item(crud_client, "Coca Cola")
    _criar_item(crud_client, "Fanta Laranja")

    resp = crud_client.get("/api/estoque/saldo?busca=coca")
    assert resp.status_code == 200
    nomes = [s["nome"] for s in resp.json()["itens"]]
    assert "Coca Cola" in nomes
    assert "Fanta Laranja" not in nomes


# ---------------------------------------------------------------------------
# Autoria e auditoria (baixa manual de estoque)
# ---------------------------------------------------------------------------

def test_baixa_sem_venda_grava_user_id_no_movimento(crud_client):
    item = _criar_item(crud_client, "Item Autoria")

    resp = _baixa(crud_client, item["id"], 3, "perda")
    assert resp.status_code == 201
    movimento_id = resp.json()["movimento"]["id"]

    db = _TestingSession()
    mov = db.get(MovimentoEstoque, movimento_id)
    db.close()

    assert mov is not None
    assert mov.user_id == _fake_user()["user_id"]


def test_baixa_sem_venda_gera_log_de_auditoria(crud_client):
    item = _criar_item(crud_client, "Item Auditado")

    resp = _baixa(crud_client, item["id"], 2, "quebra")
    assert resp.status_code == 201
    movimento_id = resp.json()["movimento"]["id"]

    db = _TestingSession()
    logs = db.query(AuditLog).filter_by(action="estoque.baixa_sem_venda").all()
    db.close()

    assert len(logs) == 1
    log = logs[0]
    assert log.user_id == _fake_user()["user_id"]
    assert log.entity == "MovimentoEstoque"
    assert log.entity_id == movimento_id


# ---------------------------------------------------------------------------
# Auditoria de insumos (create/update/toggle/delete)
# ---------------------------------------------------------------------------

def test_insumo_create_gera_log_de_auditoria(crud_client):
    item = _criar_item(crud_client, "Insumo Auditado")

    db = _TestingSession()
    logs = db.query(AuditLog).filter_by(action="insumo.create").all()
    db.close()

    assert len(logs) == 1
    assert logs[0].entity == "Insumo"
    assert logs[0].entity_id == item["id"]
    assert logs[0].user_id == _fake_user()["user_id"]


def test_insumo_update_gera_log_de_auditoria(crud_client):
    item = _criar_item(crud_client, "Insumo Original")

    resp = crud_client.put(
        f"/api/insumos/{item['id']}",
        json={"nome": "Insumo Renomeado", "unidade_base": "un"},
    )
    assert resp.status_code == 200

    db = _TestingSession()
    logs = db.query(AuditLog).filter_by(action="insumo.update").all()
    db.close()

    assert len(logs) == 1
    assert logs[0].entity_id == item["id"]


def test_insumo_toggle_ativo_gera_log_de_auditoria(crud_client):
    item = _criar_item(crud_client, "Insumo Toggle")

    resp = crud_client.patch(f"/api/insumos/{item['id']}/toggle-ativo")
    assert resp.status_code == 200

    db = _TestingSession()
    logs = db.query(AuditLog).filter_by(action="insumo.toggle_ativo").all()
    db.close()

    assert len(logs) == 1
    assert logs[0].entity_id == item["id"]


def test_insumo_delete_gera_log_de_auditoria(crud_client):
    item = _criar_item(crud_client, "Insumo Deletado")

    resp = crud_client.delete(f"/api/insumos/{item['id']}")
    assert resp.status_code == 204

    db = _TestingSession()
    logs = db.query(AuditLog).filter_by(action="insumo.delete").all()
    db.close()

    assert len(logs) == 1
    assert logs[0].entity_id == item["id"]
