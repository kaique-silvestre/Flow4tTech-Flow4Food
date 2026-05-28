import os
import datetime
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

import jwt
from fastapi import Depends
from src.api.dependencies import get_current_user, get_db, require_active_subscription
from src.core.database import Base
from src.models import billing as _billing_models  # ensure tables are created  # noqa: F401
from src.models.assinaturas import Assinatura
from src.models.tenants import Tenant
from src.repositories import billing_repository

_JWT_SECRET = "test-secret-only-for-tests-32chars!!"
_SQLITE_URL = "sqlite:///:memory:"
_engine = create_engine(_SQLITE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
_Session = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


def _override_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


def _make_token(payload: dict, exp_minutes: int = 60) -> str:
    data = {**payload, "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=exp_minutes)}
    return jwt.encode(data, _JWT_SECRET, algorithm="HS256")


@pytest.fixture
def subscription_client():
    app = FastAPI()

    @app.get("/protected")
    def _protected(user: dict = require_active_subscription):
        return {"ok": True}

    app.dependency_overrides[get_db] = _override_db
    return TestClient(app)


# --- require_active_subscription tests ---

def test_require_active_sub_passes_for_ativa():
    app = FastAPI()

    @app.get("/protected")
    def _protected(payload: dict = Depends(require_active_subscription)):
        return {"ok": True, "status": payload.get("subscription_status")}

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)
    token = _make_token({"user_id": 1, "tenant_id": 1, "subscription_status": "ativa"})
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_require_active_sub_passes_for_trial():
    app = FastAPI()

    @app.get("/protected")
    def _protected(payload: dict = Depends(require_active_subscription)):
        return {"ok": True}

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)
    token = _make_token({"user_id": 1, "tenant_id": 1, "subscription_status": "trial"})
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_require_active_sub_blocks_vencida():
    app = FastAPI()

    @app.get("/protected")
    def _protected(payload: dict = Depends(require_active_subscription)):
        return {"ok": True}

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)
    token = _make_token({"user_id": 1, "tenant_id": 1, "subscription_status": "vencida"})
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 402


def test_require_active_sub_blocks_suspensa():
    app = FastAPI()

    @app.get("/protected")
    def _protected(payload: dict = Depends(require_active_subscription)):
        return {"ok": True}

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)
    token = _make_token({"user_id": 1, "tenant_id": 1, "subscription_status": "suspensa"})
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 402


# --- billing_repository tests ---

def _create_tenant_with_assinatura(db, status: str = "ativa", data_vencimento=None):
    tenant = Tenant(nome_fantasia="Test", cnpj="00000000000001", status="ativo", created_at=datetime.datetime.now(datetime.timezone.utc))
    db.add(tenant)
    db.flush()
    db.refresh(tenant)
    assinatura = Assinatura(
        tenant_id=tenant.id,
        status=status,
        data_inicio=datetime.datetime.now(datetime.timezone.utc),
        data_vencimento=data_vencimento,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        updated_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(assinatura)
    db.commit()
    return tenant, assinatura


def test_marcar_vencidas_changes_ativa_to_vencida():
    db = _Session()
    try:
        yesterday = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
        tenant, assinatura = _create_tenant_with_assinatura(db, status="ativa", data_vencimento=yesterday)
        count = billing_repository.marcar_vencidas(db)
        assert count == 1
        db.refresh(assinatura)
        assert assinatura.status == "vencida"
    finally:
        db.close()


def test_marcar_vencidas_preserves_trial():
    db = _Session()
    try:
        yesterday = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
        tenant, assinatura = _create_tenant_with_assinatura(db, status="trial", data_vencimento=yesterday)
        count = billing_repository.marcar_vencidas(db)
        assert count == 0
        db.refresh(assinatura)
        assert assinatura.status == "trial"
    finally:
        db.close()


def test_create_plano():
    db = _Session()
    try:
        plano = billing_repository.create_plano(db, "Básico", "Plano básico", Decimal("99.90"))
        assert plano.id is not None
        assert plano.nome == "Básico"
        assert plano.ativo is True
    finally:
        db.close()


def test_create_pagamento():
    db = _Session()
    try:
        tenant = Tenant(nome_fantasia="T", cnpj="00000000000002", status="ativo", created_at=datetime.datetime.now(datetime.timezone.utc))
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        pag = billing_repository.create_pagamento(
            db,
            tenant_id=tenant.id,
            valor=Decimal("150.00"),
            data_pagamento=datetime.date.today(),
            data_vencimento=None,
            gateway_ref="PAY-123",
        )
        assert pag.id is not None
        assert pag.gateway_ref == "PAY-123"
    finally:
        db.close()
