"""Issue 2 — SELECT FOR UPDATE concurrency test (PostgreSQL only)."""

import os
import threading
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
IS_POSTGRES = DATABASE_URL.startswith("postgresql")

pytestmark = pytest.mark.skipif(
    not IS_POSTGRES,
    reason="Concurrency tests require PostgreSQL — set DATABASE_URL",
)


@pytest.fixture(scope="module")
def pg_engine():
    engine = create_engine(DATABASE_URL, future=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def pg_session_factory(pg_engine):
    return sessionmaker(bind=pg_engine, autoflush=False, autocommit=False, future=True)


def _set_tenant(session, tenant_id: int) -> None:
    session.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": str(tenant_id)})


def test_select_for_update_prevents_lost_update(pg_session_factory):
    """Two threads decrementing estoque_atual on same insumo must not lose an update."""
    from src.repositories.estoque_repository import get_insumo_for_update

    # Create test insumo
    s = pg_session_factory()
    _set_tenant(s, 1)
    result = s.execute(
        text(
            "INSERT INTO insumos (tenant_id, nome, unidade_base, estoque_atual, estoque_reservado, ativo) "
            "VALUES (1, '_cas_test_insumo', 'UNIDADE', 10, 0, true) RETURNING id"
        )
    ).fetchone()
    insumo_id = result[0]
    s.commit()
    s.close()

    errors: list[str] = []

    def decrement():
        session = pg_session_factory()
        try:
            _set_tenant(session, 1)
            insumo = get_insumo_for_update(session, insumo_id)
            if insumo is None:
                errors.append("insumo not found")
                return
            insumo.estoque_atual = insumo.estoque_atual - Decimal("1")
            session.flush()
            session.commit()
        except Exception as e:
            errors.append(str(e))
        finally:
            session.close()

    t1 = threading.Thread(target=decrement)
    t2 = threading.Thread(target=decrement)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert not errors, f"Thread errors: {errors}"

    # Verify final stock is 8 (10 - 2 decrements), not 9 (lost update)
    s = pg_session_factory()
    _set_tenant(s, 1)
    row = s.execute(
        text("SELECT estoque_atual FROM insumos WHERE id = :id"), {"id": insumo_id}
    ).fetchone()
    s.close()
    assert row is not None
    assert Decimal(str(row[0])) == Decimal("8"), f"Lost update detected, got {row[0]}"
