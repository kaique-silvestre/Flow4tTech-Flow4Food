import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests")
os.environ.setdefault("ENV", "test")

import datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_current_user, get_db
from src.core.database import Base
from src.main import app
from src.models.audit_logs import AuditLog
from src.models.comandas import Comanda
from src.models.comissoes_garcom import ComissaoGarcom
from src.models.garcons import Garcom

_SQLITE_URL = "sqlite:///:memory:"
_engine = create_engine(
    _SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSession = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def _fake_user() -> dict:
    return {"sub": "1", "user_id": 1, "tenant_id": 1, "permissions": ["cadastros", "comandas"]}


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


def _log_background_sync(action, *, tenant_id=None, user_id=None, entity=None, entity_id=None, before=None, after=None, impersonated_by=None):
    from src.services import audit_service

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
    from src.services import audit_service

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


def _criar_comissao(valor: str = "10.00", pago: bool = False) -> int:
    db = _TestingSession()
    try:
        garcom = Garcom(nome="João", ativo=True)
        db.add(garcom)
        db.commit()
        db.refresh(garcom)

        comanda = Comanda(
            identificacao="Mesa 1",
            tipo_identificacao="mesa",
            garcom_id=garcom.id,
            status="fechada",
        )
        db.add(comanda)
        db.commit()
        db.refresh(comanda)

        comissao = ComissaoGarcom(
            garcom_id=garcom.id,
            comanda_id=comanda.id,
            valor=Decimal(valor),
            percentual=Decimal("10.00"),
            pago=pago,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(comissao)
        db.commit()
        db.refresh(comissao)
        return comissao.id
    finally:
        db.close()


def test_toggle_pago_comissao_gera_log_de_auditoria(crud_client):
    comissao_id = _criar_comissao()

    resp = crud_client.patch(f"/api/garcons/comissoes/{comissao_id}/toggle-pago")
    assert resp.status_code == 200, resp.text
    assert resp.json()["pago"] is True

    db = _TestingSession()
    logs = db.query(AuditLog).filter_by(action="comissao.pago.alternar").all()
    db.close()

    assert len(logs) == 1
    assert logs[0].entity == "ComissaoGarcom"
    assert logs[0].entity_id == comissao_id


def test_delete_comissao_gera_log_de_auditoria_com_snapshot(crud_client):
    comissao_id = _criar_comissao(valor="42.50")

    resp = crud_client.delete(f"/api/garcons/comissoes/{comissao_id}")
    assert resp.status_code == 204, resp.text

    db = _TestingSession()
    logs = db.query(AuditLog).filter_by(action="comissao.remover").all()
    db.close()

    assert len(logs) == 1
    assert logs[0].entity_id == comissao_id
    assert "42.50" in (logs[0].before_data or "")


def test_update_comissao_rejeita_valor_negativo(crud_client):
    comissao_id = _criar_comissao()

    resp = crud_client.patch(f"/api/garcons/comissoes/{comissao_id}", json={"valor": -5})
    assert resp.status_code == 422


def test_update_comissao_aceita_valor_zero(crud_client):
    comissao_id = _criar_comissao()

    resp = crud_client.patch(f"/api/garcons/comissoes/{comissao_id}", json={"valor": 0})
    assert resp.status_code == 200, resp.text


def test_get_garcom_stats_404_quando_garcom_nao_existe(crud_client):
    resp = crud_client.get("/api/garcons/999999/stats")
    assert resp.status_code == 404, resp.text


def test_update_comissao_nao_duplica_query_de_leitura(crud_client):
    from sqlalchemy import event

    comissao_id = _criar_comissao()

    selects: list[str] = []

    def _on_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        normalized = statement.strip().lower()
        if normalized.startswith("select") and "comissoes_garcom" in normalized:
            selects.append(statement)

    event.listen(_engine, "before_cursor_execute", _on_cursor_execute)
    try:
        resp = crud_client.patch(f"/api/garcons/comissoes/{comissao_id}", json={"valor": "15.00"})
    finally:
        event.remove(_engine, "before_cursor_execute", _on_cursor_execute)

    assert resp.status_code == 200, resp.text
    # Antes da correção: 1 SELECT na route (pra montar o snapshot de auditoria) + 1 SELECT
    # no service (pra validar/aplicar) + 1 SELECT do `db.refresh` pós-commit = 3.
    # Depois da correção: só a leitura com lock (reaproveitada pela route) + o refresh = 2.
    assert len(selects) == 2, f"esperava 2 SELECTs em comissoes_garcom, obteve {len(selects)}: {selects}"


def _assert_log_evento_com_tenant_e_user(caplog, evento: str) -> None:
    """Encontra `evento` nos registros de `garcons_service` e confirma que veio com
    `tenant_id`/`user_id` bindados (achado: structlog do módulo sem essas chaves)."""
    import json

    eventos = [r for r in caplog.records if r.name == "src.services.garcons_service"]
    assert eventos, "esperava pelo menos um log estruturado em garcons_service"

    for record in eventos:
        payload = json.loads(record.getMessage())
        if payload.get("event") == evento:
            assert payload.get("tenant_id") == 1
            assert payload.get("user_id") == 1
            return
    pytest.fail(f"log '{evento}' não encontrado ou sem tenant_id/user_id: {eventos}")


def test_update_comissao_loga_tenant_id_e_user_id(crud_client, caplog):
    import logging

    comissao_id = _criar_comissao()

    with caplog.at_level(logging.INFO, logger="src.services.garcons_service"):
        resp = crud_client.patch(f"/api/garcons/comissoes/{comissao_id}", json={"valor": "20.00"})

    assert resp.status_code == 200, resp.text
    _assert_log_evento_com_tenant_e_user(caplog, "comissao_valor_atualizada")


def test_toggle_pago_comissao_loga_tenant_id_e_user_id(crud_client, caplog):
    import logging

    comissao_id = _criar_comissao()

    with caplog.at_level(logging.INFO, logger="src.services.garcons_service"):
        resp = crud_client.patch(f"/api/garcons/comissoes/{comissao_id}/toggle-pago")

    assert resp.status_code == 200, resp.text
    _assert_log_evento_com_tenant_e_user(caplog, "comissao_pago_alternado")
