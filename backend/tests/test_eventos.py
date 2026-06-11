import os
from datetime import datetime, timezone

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
from src.models.eventos import TenantEvento

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_Session = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def _fake_user_t1() -> dict:
    return {"sub": "1", "user_id": 1, "tenant_id": 1, "permissions": ["calendario"]}


def _fake_user_t2() -> dict:
    return {"sub": "2", "user_id": 2, "tenant_id": 2, "permissions": ["calendario"]}


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
def client():
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _fake_user_t1
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()




def _seed_evento(tenant_id: int = 1, titulo: str = "Evento Teste", data: str = "2026-06-15") -> int:
    db = _Session()
    ev = TenantEvento(
        tenant_id=tenant_id,
        titulo=titulo,
        data_evento=datetime.strptime(data, "%Y-%m-%d").date(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(ev)
    db.commit()
    eid = ev.id
    db.close()
    return eid


# E1 — CRUD completo
def test_create_evento(client):
    resp = client.post("/api/eventos", json={"titulo": "Aniversário", "data_evento": "2026-06-20"})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["titulo"] == "Aniversário"
    assert body["data_evento"] == "2026-06-20"


def test_list_eventos_by_month(client):
    _seed_evento(titulo="Junho", data="2026-06-10")
    _seed_evento(titulo="Julho", data="2026-07-05")
    resp = client.get("/api/eventos?mes=2026-06")
    assert resp.status_code == 200
    itens = resp.json()
    assert len(itens) == 1
    assert itens[0]["titulo"] == "Junho"


def test_patch_evento(client):
    eid = _seed_evento()
    resp = client.patch(f"/api/eventos/{eid}", json={"titulo": "Atualizado"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["titulo"] == "Atualizado"


def test_delete_evento(client):
    eid = _seed_evento()
    resp = client.delete(f"/api/eventos/{eid}")
    assert resp.status_code == 204, resp.text
    # confirm gone
    db = _Session()
    assert db.query(TenantEvento).filter(TenantEvento.id == eid).first() is None
    db.close()


def test_patch_not_found(client):
    resp = client.patch("/api/eventos/9999", json={"titulo": "X"})
    assert resp.status_code == 404


# E2 — GET por mês retorna só eventos do mês correto
def test_list_month_boundary(client):
    _seed_evento(titulo="Maio fim", data="2026-05-31")
    _seed_evento(titulo="Junho ini", data="2026-06-01")
    _seed_evento(titulo="Junho fim", data="2026-06-30")
    _seed_evento(titulo="Julho ini", data="2026-07-01")
    resp = client.get("/api/eventos?mes=2026-06")
    assert resp.status_code == 200
    titulos = {e["titulo"] for e in resp.json()}
    assert titulos == {"Junho ini", "Junho fim"}


# E3 — tenant_id stored correctly per tenant (SQLite; PG RLS tested via integration)
def test_rls_tenant_id_stored(client):
    _seed_evento(tenant_id=1, titulo="Do tenant 1")
    _seed_evento(tenant_id=2, titulo="Do tenant 2")

    db = _Session()
    t1_eventos = db.query(TenantEvento).filter(TenantEvento.tenant_id == 1).all()
    t2_eventos = db.query(TenantEvento).filter(TenantEvento.tenant_id == 2).all()
    db.close()
    assert len(t1_eventos) == 1
    assert t1_eventos[0].titulo == "Do tenant 1"
    assert len(t2_eventos) == 1
    assert t2_eventos[0].titulo == "Do tenant 2"
