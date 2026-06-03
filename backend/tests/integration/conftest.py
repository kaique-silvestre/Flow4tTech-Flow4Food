"""
Integration test fixtures.

Requires a real PostgreSQL database (DATABASE_URL must start with "postgresql").
In CI, the database is already migrated via `alembic upgrade head` before tests run.

All test data uses tenant IDs 999901/999902 to avoid conflicts with real data.
Cleanup runs after each module via autouse fixtures.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

# Skip entire module if not PostgreSQL (e.g. local dev without DB)
_db_url = os.environ.get("DATABASE_URL", "")
if not _db_url.startswith("postgresql"):
    pytest.skip("Integration tests require PostgreSQL", allow_module_level=True)

from src.core.database import SessionLocal  # noqa: E402 — must be after env check
from src.main import app  # noqa: E402

TENANT_A = 999901
TENANT_B = 999902
PASSWORD = "IntegrationTest123!"


@pytest.fixture(scope="module")
def db():
    """Direct DB session for seeding and verification. Runs as DB superuser, bypasses RLS."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module", autouse=True)
def seed_tenants(db):
    """Seed two isolated tenants with users and assinaturas. Clean up after the module."""
    # Tenants
    db.execute(text(
        "INSERT INTO tenants (id, nome_fantasia, status) VALUES "
        "(:a, 'Integration Tenant A', 'ativo'), "
        "(:b, 'Integration Tenant B', 'ativo') "
        "ON CONFLICT (id) DO NOTHING"
    ), {"a": TENANT_A, "b": TENANT_B})

    # Profiles (one per tenant, full access)
    for tid, profile_id in [(TENANT_A, 99990), (TENANT_B, 99991)]:
        db.execute(text(
            "INSERT INTO profiles (id, tenant_id, name, is_system, is_active) "
            "VALUES (:pid, :tid, 'Test Admin', true, true) "
            "ON CONFLICT (id) DO NOTHING"
        ), {"pid": profile_id, "tid": tid})

    # Profile permissions: grant all known screens
    screens = [
        "cadastros", "vendas", "estoque", "compras",
        "financeiro", "relatorios", "dashboard", "config",
    ]
    perm_id = 999900
    for profile_id in (99990, 99991):
        tid = TENANT_A if profile_id == 99990 else TENANT_B
        for screen in screens:
            db.execute(text(
                "INSERT INTO profile_permissions (id, tenant_id, profile_id, screen, can_access) "
                "VALUES (:pid, :tid, :profile_id, :screen, true) "
                "ON CONFLICT (id) DO NOTHING"
            ), {"pid": perm_id, "tid": tid, "profile_id": profile_id, "screen": screen})
            perm_id += 1

    # System users
    from src.services.auth_service import hash_password as _hash

    hashed = _hash(PASSWORD)
    db.execute(text(
        "INSERT INTO system_users "
        "(id, tenant_id, profile_id, name, username, email, password_hash, is_active) "
        "VALUES "
        "(999901, :ta, 99990, 'User Tenant A', 'integration_user_a', 'a@integration.test', :pw, true), "
        "(999902, :tb, 99991, 'User Tenant B', 'integration_user_b', 'b@integration.test', :pw, true) "
        "ON CONFLICT (id) DO NOTHING"
    ), {"ta": TENANT_A, "tb": TENANT_B, "pw": hashed})

    # Assinaturas (required for subscription_status in JWT)
    db.execute(text(
        "INSERT INTO assinaturas (tenant_id, status) VALUES "
        "(:a, 'ativa'), (:b, 'ativa') "
        "ON CONFLICT (tenant_id) DO NOTHING"
    ), {"a": TENANT_A, "b": TENANT_B})

    db.commit()

    yield

    # Cleanup in FK-safe order
    # Note: refresh_tokens cascade-deletes when system_users rows are deleted (ondelete=CASCADE)
    # Note: revoked_tokens has no user_id FK — skipped (rows expire naturally via scheduler)
    db.execute(text("DELETE FROM categorias WHERE tenant_id IN (:a, :b)"), {"a": TENANT_A, "b": TENANT_B})
    db.execute(text("DELETE FROM system_users WHERE tenant_id IN (:a, :b)"), {"a": TENANT_A, "b": TENANT_B})
    db.execute(text("DELETE FROM profile_permissions WHERE tenant_id IN (:a, :b)"), {"a": TENANT_A, "b": TENANT_B})
    db.execute(text("DELETE FROM profiles WHERE tenant_id IN (:a, :b)"), {"a": TENANT_A, "b": TENANT_B})
    db.execute(text("DELETE FROM assinaturas WHERE tenant_id IN (:a, :b)"), {"a": TENANT_A, "b": TENANT_B})
    db.execute(text("DELETE FROM tenants WHERE id IN (:a, :b)"), {"a": TENANT_A, "b": TENANT_B})
    db.commit()


@pytest.fixture(scope="module")
def client():
    """TestClient using the real DB — no dependency overrides."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="module")
def token_a(client):
    """Access token for tenant A user."""
    resp = client.post("/api/auth/login", json={
        "identifier": "integration_user_a",
        "password": PASSWORD,
    })
    assert resp.status_code == 200, f"Login tenant A failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="module")
def token_b(client):
    """Access token for tenant B user."""
    resp = client.post("/api/auth/login", json={
        "identifier": "integration_user_b",
        "password": PASSWORD,
    })
    assert resp.status_code == 200, f"Login tenant B failed: {resp.text}"
    return resp.json()["access_token"]


def auth(token: str) -> dict:
    """Helper: build Authorization header dict."""
    return {"Authorization": f"Bearer {token}"}
