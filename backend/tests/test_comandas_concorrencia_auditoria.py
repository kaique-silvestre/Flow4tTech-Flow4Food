"""Testes de concorrência otimista (fechar/reabrir/patch), N+1 na listagem
de comandas abertas e trilha de auditoria em fechar/cancelar comanda."""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests")
os.environ.setdefault("ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.api.dependencies import get_current_user, get_db
from src.core.database import Base
from src.main import app
from src.models.audit_logs import AuditLog
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
    """Roda audit_service.log de forma síncrona, na mesma base de testes, no lugar
    do log_background real (que abre uma sessão separada de plataforma)."""
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
def c(monkeypatch):
    def override_get_db():
        db = _TestingSession()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(audit_service, "log_background", _log_background_sync)
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
        json={"identificacao": identificacao, "tipo_identificacao": "mesa", "garcom_id": garcom_id, "pessoas": ["Cliente 1"]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _lancar_item(c, comanda_id, item_id, version, quantidade=1):
    resp = c.post(
        f"/api/comandas/{comanda_id}/itens",
        json={"item_id": item_id, "quantidade": quantidade, "version": version},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _fechar(c, comanda_id, metodo_id, valor, version, modo="sem_divisao"):
    return c.post(
        f"/api/comandas/{comanda_id}/fechar",
        json={
            "pagamentos": [{"metodo_id": metodo_id, "valor": str(valor)}],
            "modo_divisao": modo,
            "version": version,
        },
    )


def _reabrir(c, comanda_id, version):
    return c.post(f"/api/comandas/{comanda_id}/reabrir", json={"version": version})


def _patch(c, comanda_id, version, **kwargs):
    body = {"version": version, **kwargs}
    return c.patch(f"/api/comandas/{comanda_id}", json=body)


def _count_queries(fn):
    """Executa fn() contando quantos statements SQL são disparados no engine de testes."""
    count = 0

    def _on_execute(*_args, **_kwargs):
        nonlocal count
        count += 1

    event.listen(_engine, "before_cursor_execute", _on_execute)
    try:
        result = fn()
    finally:
        event.remove(_engine, "before_cursor_execute", _on_execute)
    return result, count


# ---------------------------------------------------------------------------
# Optimistic locking: fechar_comanda
# ---------------------------------------------------------------------------


def test_fechar_comanda_version_desatualizada_retorna_409(c):
    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="30.00")
    metodo = _criar_metodo(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]

    r = _lancar_item(c, cid, item["id"], comanda["version"])

    resp = _fechar(c, cid, metodo["id"], "30.00", version=999)
    assert resp.status_code == 409, resp.text
    assert resp.json()["error"]["code"] == "COMANDA_DESATUALIZADA"

    # comanda permanece aberta e não foi fechada
    assert c.get(f"/api/comandas/{cid}").json()["status"] == "aberta"
    _ = r


def test_fechar_comanda_dois_requests_concorrentes_um_sucede_outro_falha():
    """Simula duplo clique / retry de rede: dois POSTs /fechar com a mesma
    version (a versão lida por ambos antes de qualquer um commitar) — apenas
    um deve suceder (200) e o outro deve falhar (409 desatualizada, ou 400 se
    o primeiro já fechou a comanda), e nenhum pagamento duplicado é criado."""
    from src.models.pagamentos import Pagamento

    def override_get_db():
        db = _TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _fake_user
    try:
        with TestClient(app) as c:
            garcom = _criar_garcom(c)
            item = _criar_item(c, preco="30.00")
            metodo = _criar_metodo(c)
            comanda = _abrir_comanda(c, garcom["id"])
            cid = comanda["id"]
            r = _lancar_item(c, cid, item["id"], comanda["version"])
            version = r["version"]

            resp1 = _fechar(c, cid, metodo["id"], "30.00", version)
            resp2 = _fechar(c, cid, metodo["id"], "30.00", version)

            codes = sorted([resp1.status_code, resp2.status_code])
            assert codes[0] in (200,) and codes[1] in (400, 409), (resp1.text, resp2.text)
            assert 200 in (resp1.status_code, resp2.status_code)

            db: Session = _TestingSession()
            try:
                count = db.query(Pagamento).filter(Pagamento.comanda_id == cid).count()
                assert count == 1
            finally:
                db.close()
    finally:
        app.dependency_overrides.clear()


def test_increment_version_e_atomico_apenas_uma_chamada_sucede(c):
    """Prova de baixo nível do CAS usado pelo lock otimista: duas tentativas
    de incrementar a partir da MESMA version — apenas uma retorna True."""
    from src.repositories import comandas_repository

    garcom = _criar_garcom(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]

    db = _TestingSession()
    try:
        ok1 = comandas_repository.increment_version(db, cid, comanda["version"], 1)
        ok2 = comandas_repository.increment_version(db, cid, comanda["version"], 1)
        db.commit()

        assert ok1 is True
        assert ok2 is False
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Optimistic locking: reabrir_comanda
# ---------------------------------------------------------------------------


def test_reabrir_comanda_version_desatualizada_retorna_409(c):
    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="30.00")
    metodo = _criar_metodo(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]

    r = _lancar_item(c, cid, item["id"], comanda["version"])
    fechado = _fechar(c, cid, metodo["id"], "30.00", r["version"]).json()

    resp = _reabrir(c, cid, version=999)
    assert resp.status_code == 409, resp.text
    assert resp.json()["error"]["code"] == "COMANDA_DESATUALIZADA"
    assert c.get(f"/api/comandas/{cid}").json()["status"] == "fechada"
    _ = fechado


# ---------------------------------------------------------------------------
# Optimistic locking: patch_comanda
# ---------------------------------------------------------------------------


def test_patch_comanda_version_desatualizada_retorna_409(c):
    garcom = _criar_garcom(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]

    resp = _patch(c, cid, version=999, identificacao="Mesa 9")
    assert resp.status_code == 409, resp.text
    assert resp.json()["error"]["code"] == "COMANDA_DESATUALIZADA"
    assert c.get(f"/api/comandas/{cid}").json()["identificacao"] != "Mesa 9"


def test_patch_comanda_version_correta_aplica_e_incrementa(c):
    garcom = _criar_garcom(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]

    resp = _patch(c, cid, version=comanda["version"], identificacao="Mesa 9")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["identificacao"] == "Mesa 9"
    assert data["version"] == comanda["version"] + 1


# ---------------------------------------------------------------------------
# N+1 na listagem de comandas abertas
# ---------------------------------------------------------------------------


def test_list_comandas_abertas_nao_escala_linearmente_com_itens(c):
    """Várias comandas com vários itens cada não devem gerar 1 query por item/
    comanda — o total de queries deve ficar limitado a um pequeno número fixo,
    independentemente de quantas comandas/itens existirem."""
    garcom = _criar_garcom(c)
    metodo = _criar_metodo(c)
    item = _criar_item(c, preco="10.00")
    _ = metodo

    n_comandas = 8
    itens_por_comanda = 4
    for i in range(n_comandas):
        comanda = _abrir_comanda(c, garcom["id"], identificacao=f"Mesa {i}")
        cid = comanda["id"]
        version = comanda["version"]
        for _j in range(itens_por_comanda):
            r = _lancar_item(c, cid, item["id"], version)
            version = r["version"]

    _, queries = _count_queries(lambda: c.get("/api/comandas"))

    resp = c.get("/api/comandas")
    assert resp.status_code == 200
    assert len(resp.json()) == n_comandas

    # Sem o batching, seriam ~n_comandas * (1 garcom + itens_por_comanda*(1
    # produto) + pagamentos) queries — bem mais que n_comandas. Com batching,
    # o total fica preso a um pequeno número fixo de queries (garçons, itens,
    # produtos, promoções, pagamentos, métodos), não escalando com n_comandas
    # nem com itens_por_comanda.
    assert queries <= 10, f"esperado poucas queries fixas (<=10), obteve {queries}"


# ---------------------------------------------------------------------------
# Auditoria: fechar_comanda / cancelar_comanda
# ---------------------------------------------------------------------------


def test_fechar_comanda_gera_log_de_auditoria(c):
    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="30.00")
    metodo = _criar_metodo(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]
    r = _lancar_item(c, cid, item["id"], comanda["version"])

    resp = _fechar(c, cid, metodo["id"], "30.00", r["version"])
    assert resp.status_code == 200, resp.text

    db: Session = _TestingSession()
    try:
        logs = db.query(AuditLog).filter(AuditLog.action == "comanda.fechar", AuditLog.entity_id == cid).all()
        assert len(logs) == 1
    finally:
        db.close()


def test_cancelar_comanda_gera_log_de_auditoria(c):
    garcom = _criar_garcom(c)
    comanda = _abrir_comanda(c, garcom["id"])
    cid = comanda["id"]

    resp = c.post(f"/api/comandas/{cid}/cancelar", json={"version": comanda["version"]})
    assert resp.status_code == 200, resp.text

    db: Session = _TestingSession()
    try:
        logs = db.query(AuditLog).filter(AuditLog.action == "comanda.cancelar", AuditLog.entity_id == cid).all()
        assert len(logs) == 1
    finally:
        db.close()
