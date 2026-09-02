import os
from datetime import datetime, timezone

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("DATABASE_URL_PLATFORM", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_current_user, get_db
from src.core.database import Base, get_platform_db
from src.core.limiter import limiter
from src.main import app
from src.models.platform_admin import PlatformAdmin
from src.services.auth_service import hash_password

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


@pytest.fixture
def rate_limiting_enabled():
    """Rate limiting is disabled globally under ENV=test (see core/limiter.py)
    so the rest of the suite can hammer endpoints freely. Flip it on for the
    duration of a single test and reset the counters so tests don't bleed
    into each other."""
    limiter.enabled = True
    limiter.reset()
    yield
    limiter.reset()
    limiter.enabled = False


def _override_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def platform_client():
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_platform_db] = _override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _fake_caixa_user() -> dict:
    return {"sub": "1", "user_id": 1, "tenant_id": 1, "permissions": ["caixa", "cadastros"]}


@pytest.fixture
def tenant_client():
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _fake_caixa_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _seed_admin(email: str = "admin@platform.com", password: str = "correct-password") -> PlatformAdmin:
    db = _Session()
    admin = PlatformAdmin(
        email=email,
        name="Platform Admin",
        password_hash=hash_password(password),
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    db.close()
    return admin


def test_platform_login_rate_limited_after_5_attempts(platform_client, rate_limiting_enabled):
    _seed_admin()
    for _ in range(5):
        resp = platform_client.post(
            "/api/platform/auth/login",
            json={"email": "admin@platform.com", "password": "wrong"},
        )
        assert resp.status_code == 401, resp.text

    resp = platform_client.post(
        "/api/platform/auth/login",
        json={"email": "admin@platform.com", "password": "wrong"},
    )
    assert resp.status_code == 429, resp.text


def test_caixa_get_sessao_rate_limited(tenant_client, rate_limiting_enabled):
    limit = 60
    for _ in range(limit):
        resp = tenant_client.get("/api/caixa/sessao")
        assert resp.status_code == 404, resp.text

    resp = tenant_client.get("/api/caixa/sessao")
    assert resp.status_code == 429, resp.text


def test_garcons_delete_comissao_rate_limited(tenant_client, rate_limiting_enabled):
    limit = 30
    for _ in range(limit):
        resp = tenant_client.delete("/api/garcons/comissoes/999999")
        assert resp.status_code == 404, resp.text

    resp = tenant_client.delete("/api/garcons/comissoes/999999")
    assert resp.status_code == 429, resp.text
