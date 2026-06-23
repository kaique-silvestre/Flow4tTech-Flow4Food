import os
import datetime

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
from src.models.contas_pagar import ContaPagar
from src.models.compras import Compra
from src.models.eventos import TenantEvento

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_Session = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def _fake_all_perms() -> dict:
    return {
        "sub": "1",
        "user_id": 1,
        "tenant_id": 1,
        "permissions": ["calendario", "financeiro", "estoque"],
    }


def _fake_no_financeiro() -> dict:
    return {
        "sub": "1",
        "user_id": 1,
        "tenant_id": 1,
        "permissions": ["calendario", "estoque"],
    }



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


@pytest.fixture
def db_session():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client_all(db_session):
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _fake_all_perms
    with TestClient(app) as c:
        yield c, db_session
    app.dependency_overrides.clear()


@pytest.fixture
def client_no_financeiro(db_session):
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _fake_no_financeiro
    with TestClient(app) as c:
        yield c, db_session
    app.dependency_overrides.clear()




def _seed_conta(db, tenant_id: int = 1, data: str = "2026-06-15") -> int:
    conta = ContaPagar(
        tenant_id=tenant_id,
        valor="100.00",
        data_vencimento=datetime.date.fromisoformat(data),
        status="pendente",
        created_at=datetime.datetime(2026, 6, 1, tzinfo=datetime.timezone.utc),
    )
    db.add(conta)
    db.commit()
    db.refresh(conta)
    return conta.id


def _seed_compra(db, tenant_id: int = 1, data: str = "2026-06-20") -> int:
    compra = Compra(
        tenant_id=tenant_id,
        data_compra=datetime.date(2026, 6, 1),
        total="50.00",
        status="confirmado",
        tipo_compra="agendada",
        data_prevista_recebimento=datetime.date.fromisoformat(data),
        created_at=datetime.datetime(2026, 6, 1, tzinfo=datetime.timezone.utc),
    )
    db.add(compra)
    db.commit()
    db.refresh(compra)
    return compra.id


def _seed_evento(db, tenant_id: int = 1, data: str = "2026-06-10") -> int:
    ev = TenantEvento(
        tenant_id=tenant_id,
        titulo="Evento Test",
        data_evento=datetime.date.fromisoformat(data),
        created_at=datetime.datetime(2026, 6, 1, tzinfo=datetime.timezone.utc),
        updated_at=datetime.datetime(2026, 6, 1, tzinfo=datetime.timezone.utc),
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev.id


# D1 — sem financeiro → sem conta_pagar
def test_sem_financeiro_sem_conta_pagar(client_no_financeiro):
    client, db = client_no_financeiro
    _seed_conta(db, tenant_id=1)
    resp = client.get("/api/calendario/consolidado", params={"mes": "2026-06"})
    assert resp.status_code == 200
    tipos = [i["tipo"] for i in resp.json()]
    assert "conta_pagar" not in tipos


# D2 — todas as permissões → conta_pagar e entrega_insumo presentes
def test_todas_permissoes_todas_camadas(client_all):
    client, db = client_all
    _seed_conta(db, tenant_id=1)
    _seed_compra(db, tenant_id=1)
    _seed_evento(db, tenant_id=1)
    resp = client.get("/api/calendario/consolidado", params={"mes": "2026-06"})
    assert resp.status_code == 200
    tipos = {i["tipo"] for i in resp.json()}
    assert "conta_pagar" in tipos
    assert "entrega_insumo" in tipos
    assert "evento" in tipos


# D3 — items pertencentes ao tenant correto aparecem no response
def test_tenant_own_data_visible(client_all):
    client, db = client_all
    _seed_conta(db, tenant_id=1)
    _seed_evento(db, tenant_id=1)
    resp = client.get("/api/calendario/consolidado", params={"mes": "2026-06"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    # All returned items reference seeded date range
    for item in data:
        assert item["data_referencia"].startswith("2026-06")
