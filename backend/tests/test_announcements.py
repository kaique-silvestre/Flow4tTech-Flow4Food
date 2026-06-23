import os
from datetime import datetime, timezone, timedelta

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_db
from src.core.database import Base, get_platform_db
from src.main import app
from src.repositories import announcements_repository
from src.services.auth_service import create_access_token

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
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


@pytest.fixture
def db():
    session = _Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_platform_db] = _override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _platform_token() -> str:
    return create_access_token(
        {"platform_admin": True, "admin_id": 1, "email": "admin@platform.com"}
    )


def _tenant_token(tenant_id: int = 1, user_id: int = 10) -> str:
    return create_access_token({"user_id": user_id, "tenant_id": tenant_id, "permissions": []})


# ── Repository tests ──────────────────────────────────────────────────────────

def test_create_broadcast_announcement(db):
    now = datetime.now(timezone.utc)
    ann = announcements_repository.create(
        db,
        title="Manutenção programada",
        body="Sistema offline às 2h",
        expires_at=None,
        target="all",
        tenant_ids=[],
        created_by=None,
    )
    assert ann.id is not None
    assert ann.title == "Manutenção programada"
    assert ann.target == "all"
    assert ann.is_active is True


def test_list_active_for_user_returns_broadcast(db):
    announcements_repository.create(
        db,
        title="Aviso geral",
        body="Corpo",
        expires_at=None,
        target="all",
        tenant_ids=[],
        created_by=None,
    )
    items = announcements_repository.list_active_for_user(db, tenant_id=1, user_id=99)
    assert len(items) == 1
    assert items[0].title == "Aviso geral"


def test_list_active_excludes_expired(db):
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    announcements_repository.create(
        db,
        title="Expirado",
        body="Corpo",
        expires_at=past,
        target="all",
        tenant_ids=[],
        created_by=None,
    )
    items = announcements_repository.list_active_for_user(db, tenant_id=1, user_id=99)
    assert items == []


def test_list_active_excludes_already_read(db):
    ann = announcements_repository.create(
        db,
        title="Lido",
        body="Corpo",
        expires_at=None,
        target="all",
        tenant_ids=[],
        created_by=None,
    )
    announcements_repository.mark_read(db, ann.id, user_id=5, tenant_id=1)
    items = announcements_repository.list_active_for_user(db, tenant_id=1, user_id=5)
    assert items == []


def test_list_active_specific_target_correct_tenant(db):
    ann = announcements_repository.create(
        db,
        title="Só tenant 2",
        body="Corpo",
        expires_at=None,
        target="specific",
        tenant_ids=[2],
        created_by=None,
    )
    items_t2 = announcements_repository.list_active_for_user(db, tenant_id=2, user_id=99)
    items_t1 = announcements_repository.list_active_for_user(db, tenant_id=1, user_id=99)
    assert len(items_t2) == 1
    assert items_t1 == []


def test_mark_read_idempotent(db):
    ann = announcements_repository.create(
        db,
        title="Idempotente",
        body="Corpo",
        expires_at=None,
        target="all",
        tenant_ids=[],
        created_by=None,
    )
    announcements_repository.mark_read(db, ann.id, user_id=7, tenant_id=1)
    announcements_repository.mark_read(db, ann.id, user_id=7, tenant_id=1)
    items = announcements_repository.list_active_for_user(db, tenant_id=1, user_id=7)
    assert items == []


def test_list_with_read_counts(db):
    ann = announcements_repository.create(
        db, title="A", body="B", expires_at=None, target="all", tenant_ids=[], created_by=None
    )
    announcements_repository.mark_read(db, ann.id, user_id=1, tenant_id=1)
    announcements_repository.mark_read(db, ann.id, user_id=2, tenant_id=1)
    rows = announcements_repository.list_with_read_counts(db)
    assert rows[0]["read_count"] == 2


# ── API tests ─────────────────────────────────────────────────────────────────

def test_platform_create_announcement(client):
    resp = client.post(
        "/api/platform/announcements",
        json={"title": "Novo aviso", "body": "Texto", "target": "all"},
        headers={"Authorization": f"Bearer {_platform_token()}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Novo aviso"
    assert data["read_count"] == 0


def test_platform_list_announcements(client):
    client.post(
        "/api/platform/announcements",
        json={"title": "X", "body": "Y", "target": "all"},
        headers={"Authorization": f"Bearer {_platform_token()}"},
    )
    resp = client.get(
        "/api/platform/announcements",
        headers={"Authorization": f"Bearer {_platform_token()}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_platform_create_requires_auth(client):
    resp = client.post(
        "/api/platform/announcements",
        json={"title": "X", "body": "Y"},
    )
    assert resp.status_code == 401


def test_app_get_active_announcements(client):
    client.post(
        "/api/platform/announcements",
        json={"title": "Aviso app", "body": "Corpo", "target": "all"},
        headers={"Authorization": f"Bearer {_platform_token()}"},
    )
    resp = client.get(
        "/api/app/announcements",
        headers={"Authorization": f"Bearer {_tenant_token()}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["title"] == "Aviso app"


def test_app_mark_announcement_read(client):
    create_resp = client.post(
        "/api/platform/announcements",
        json={"title": "Leitura", "body": "Corpo", "target": "all"},
        headers={"Authorization": f"Bearer {_platform_token()}"},
    )
    ann_id = create_resp.json()["id"]

    mark_resp = client.post(
        f"/api/app/announcements/{ann_id}/read",
        headers={"Authorization": f"Bearer {_tenant_token()}"},
    )
    assert mark_resp.status_code == 204

    get_resp = client.get(
        "/api/app/announcements",
        headers={"Authorization": f"Bearer {_tenant_token()}"},
    )
    assert get_resp.json() == []


def test_app_announcements_requires_auth(client):
    resp = client.get("/api/app/announcements")
    assert resp.status_code == 401
