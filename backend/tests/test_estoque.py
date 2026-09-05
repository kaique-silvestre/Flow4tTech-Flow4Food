import os
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests")
os.environ.setdefault("ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_current_user, get_db
from src.core.database import Base
from src.core.errors import AppError, ErrorCode
from src.main import app
from src.models.audit_logs import AuditLog
from src.models.ficha_tecnica import FichaTecnica
from src.models.insumos import Insumo, UnidadeBase
from src.models.movimentos_estoque import MovimentoEstoque
from src.models.produtos import Produto
from src.repositories import estoque_repository
from src.schemas.estoque import BaixaSemVendaRequest
from src.services import audit_service, estoque_service

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


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("post", "/api/insumos", {"nome": "Caixa negativa", "unidade_base": "un", "quantidade_caixa": -1}),
        ("put", "/api/insumos/999", {"nome": "Nível negativo", "unidade_base": "un", "nivel_critico": -1}),
    ],
)
def test_insumo_rejeita_valores_negativos(crud_client, method, path, payload):
    resp = getattr(crud_client, method)(path, json=payload)

    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("endpoint", [
    "/api/estoque/movimentos?data_inicio=nao-e-uma-data",
    "/api/estoque/movimentos-produtos?data_fim=2026-99-99",
])
def test_historicos_rejeitam_datas_malformadas_com_erro_de_validacao(crud_client, endpoint):
    resp = crud_client.get(endpoint)

    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_ajuste_de_ficha_trava_insumos_em_ordem_deterministica():
    db = _TestingSession()
    try:
        produto = Produto(nome="Produto", preco_venda=Decimal("10"))
        primeiro = Insumo(nome="Primeiro", unidade_base=UnidadeBase.UNIDADE)
        segundo = Insumo(nome="Segundo", unidade_base=UnidadeBase.UNIDADE)
        db.add_all([produto, primeiro, segundo])
        db.flush()
        # Insert in reverse order to prove that the locking order does not
        # depend on ficha insertion order.
        db.add_all([
            FichaTecnica(produto_id=produto.id, insumo_id=segundo.id, quantidade=Decimal("1")),
            FichaTecnica(produto_id=produto.id, insumo_id=primeiro.id, quantidade=Decimal("1")),
        ])
        db.commit()

        locked_ids: list[int] = []
        estoque_repository.ajustar_estoque_ficha_tecnica(
            db,
            produto.id,
            Decimal("1"),
            lambda insumo, _quantidade: locked_ids.append(insumo.id),
        )

        assert locked_ids == sorted(locked_ids)
    finally:
        db.close()


def test_baixa_manual_defende_contra_insumo_de_outro_tenant():
    db = _TestingSession()
    try:
        insumo = Insumo(nome="Insumo isolado", unidade_base=UnidadeBase.UNIDADE, tenant_id=2)
        db.add(insumo)
        db.commit()

        with pytest.raises(AppError) as exc_info:
            estoque_service.baixa_sem_venda(
                db,
                BaixaSemVendaRequest(item_id=insumo.id, quantidade=Decimal("1"), motivo="perda"),
                tenant_id=1,
            )

        assert exc_info.value.code == ErrorCode.NOT_FOUND
    finally:
        db.close()


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
