"""Issue #28 — check_subscription blocks 402 for suspended/cancelled/expired tenants."""
import datetime
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import check_subscription, get_db
from src.core.database import Base, get_platform_db
from src.core.errors import register_exception_handlers
from src.models.assinaturas import Assinatura
from src.models.platform_settings import PlatformSettings
from src.models.tenants import Tenant

_JWT_SECRET = "test-secret-only-for-tests-32chars!!"
_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
_Session = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(_engine)
    # Seed contact_email — pass updated_at explicitly (SQLite has no NOW())
    now = datetime.datetime.now(datetime.timezone.utc)
    db = _Session()
    db.add(PlatformSettings(key="contact_email", value="suporte@flow4tech.com.br", updated_at=now))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(_engine)


def _override_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


def _make_token(tenant_id: int, exp_minutes: int = 60) -> str:
    payload = {
        "user_id": 1,
        "tenant_id": tenant_id,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=exp_minutes),
        "jti": "test-jti",
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm="HS256")


def _make_app():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/protected")
    def _protected(payload: dict = Depends(check_subscription)):
        return {"ok": True, "tenant_id": payload.get("tenant_id")}

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_platform_db] = _override_db
    return TestClient(app)


def _add_assinatura(tenant_id: int, status: str, data_vencimento=None):
    now = datetime.datetime.now(datetime.timezone.utc)
    db = _Session()
    db.add(Tenant(id=tenant_id, nome_fantasia="Teste", cnpj="00000000000100", status="ativo", created_at=now))
    db.add(Assinatura(
        tenant_id=tenant_id,
        status=status,
        data_vencimento=data_vencimento,
        data_inicio=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        created_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        updated_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
    ))
    db.commit()
    db.close()


def test_ativa_passes():
    _add_assinatura(1, "ativa")
    client = _make_app()
    token = _make_token(1)
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_trial_sem_vencimento_passes():
    _add_assinatura(2, "trial", data_vencimento=None)
    client = _make_app()
    token = _make_token(2)
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_trial_vencimento_futuro_passes():
    future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=5)
    _add_assinatura(3, "trial", data_vencimento=future)
    client = _make_app()
    token = _make_token(3)
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_suspensa_blocked():
    _add_assinatura(4, "suspensa")
    client = _make_app()
    token = _make_token(4)
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 402
    body = resp.json()
    assert body["detail"]["code"] == "SUBSCRIPTION_BLOCKED"
    assert body["detail"]["status"] == "suspensa"
    assert body["detail"]["contact"] == "suporte@flow4tech.com.br"


def test_cancelada_blocked():
    _add_assinatura(5, "cancelada")
    client = _make_app()
    token = _make_token(5)
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 402
    body = resp.json()
    assert body["detail"]["code"] == "SUBSCRIPTION_BLOCKED"
    assert body["detail"]["status"] == "cancelada"


def test_trial_vencido_blocked():
    past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    _add_assinatura(6, "trial", data_vencimento=past)
    client = _make_app()
    token = _make_token(6)
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 402
    body = resp.json()
    assert body["detail"]["code"] == "SUBSCRIPTION_BLOCKED"
    assert body["detail"]["status"] == "trial"


def test_no_assinatura_passes():
    """Tenant sem assinatura não é bloqueado (data inconsistente — libera acesso)."""
    now = datetime.datetime.now(datetime.timezone.utc)
    db = _Session()
    db.add(Tenant(id=7, nome_fantasia="Sem Sub", cnpj="00000000000107", status="ativo", created_at=now))
    db.commit()
    db.close()
    client = _make_app()
    token = _make_token(7)
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
