"""RLS tenant isolation tests — PostgreSQL only (skipped on SQLite)."""

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
IS_POSTGRES = DATABASE_URL.startswith("postgresql")

pytestmark = pytest.mark.skipif(
    not IS_POSTGRES,
    reason="RLS tests require PostgreSQL — set DATABASE_URL to a postgres connection",
)


@pytest.fixture(scope="module")
def pg_engine():
    engine = create_engine(DATABASE_URL, future=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def pg_session(pg_engine):
    Session = sessionmaker(bind=pg_engine, autoflush=False, autocommit=False, future=True)
    session = Session()
    yield session
    session.close()


def _seed_tenant(session, tenant_id: int) -> None:
    session.execute(
        text(
            "INSERT INTO tenants (id, nome_fantasia, status) "
            "VALUES (:id, :nome, 'ativo') ON CONFLICT (id) DO NOTHING"
        ),
        {"id": tenant_id, "nome": f"Tenant {tenant_id}"},
    )


def _seed_categoria(session, tenant_id: int, nome: str) -> int:
    row = session.execute(
        text(
            "INSERT INTO categorias (tenant_id, nome) VALUES (:tid, :nome) "
            "ON CONFLICT DO NOTHING RETURNING id"
        ),
        {"tid": tenant_id, "nome": nome},
    ).fetchone()
    return row[0] if row else None


def test_rls_isolation_between_tenants(pg_session):
    """Query with app.tenant_id=1 must not return rows belonging to tenant_id=2."""
    session = pg_session
    _seed_tenant(session, 1)
    _seed_tenant(session, 2)
    _seed_categoria(session, 1, "_rls_test_cat_t1")
    _seed_categoria(session, 2, "_rls_test_cat_t2")
    session.commit()

    # Set tenant context to tenant 1
    session.execute(text("SET app.tenant_id = '1'"))
    rows = session.execute(
        text("SELECT tenant_id FROM categorias WHERE nome LIKE '_rls_test_cat_%'")
    ).fetchall()
    tenant_ids_visible = {r[0] for r in rows}

    assert 1 in tenant_ids_visible, "Tenant 1 should see its own rows"
    assert 2 not in tenant_ids_visible, "Tenant 1 must NOT see tenant 2 rows"


def test_rls_blocks_without_setting(pg_session):
    """Query without SET app.tenant_id must return 0 rows (RLS blocks all)."""
    session = pg_session

    # Reset setting — use empty string so NULLIF returns NULL
    session.execute(text("SET app.tenant_id = ''"))
    rows = session.execute(
        text("SELECT id FROM categorias WHERE nome LIKE '_rls_test_cat_%'")
    ).fetchall()

    assert len(rows) == 0, "Without app.tenant_id, RLS must block all rows"
