from unittest.mock import MagicMock

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from src.core import tenant_rls


def _pg_session() -> MagicMock:
    db = MagicMock()
    db.get_bind.return_value.dialect.name = "postgresql"
    return db


def test_arm_sets_role_then_tenant_id_in_order() -> None:
    db = _pg_session()

    tenant_rls.arm(db, 7)

    calls = db.execute.call_args_list
    assert "SET ROLE app_user" in str(calls[0].args[0])
    assert "SET app.tenant_id" in str(calls[1].args[0])
    assert calls[1].args[1] == {"tid": "7"}


def test_clear_resets_role_then_tenant_id_in_order() -> None:
    db = _pg_session()

    tenant_rls.clear(db)

    calls = db.execute.call_args_list
    assert "RESET ROLE" in str(calls[0].args[0])
    assert "SET app.tenant_id = ''" in str(calls[1].args[0])


def test_arm_sets_tenant_ctx_and_clear_resets_it() -> None:
    db = _pg_session()

    tenant_rls.arm(db, 9)
    assert tenant_rls._tenant_ctx.tenant_id == 9

    tenant_rls.clear(db)
    assert tenant_rls._tenant_ctx.tenant_id is None


def test_arm_and_clear_are_noops_on_sqlite() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine, future=True)
    db = Session()
    try:
        tenant_rls.arm(db, 7)
        tenant_rls.clear(db)
        assert db.get_bind().dialect.name == "sqlite"
    finally:
        db.close()
