import os

# Provide minimal env BEFORE importing app/settings.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

import sqlalchemy as sa
import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_db
from src.main import app

# Patch PostgreSQL-specific server_defaults for SQLite test compatibility.
# Models use current_setting('app.tenant_id') which only exists in PostgreSQL.
from src.core.database import Base

for _table in Base.metadata.tables.values():
    for _col in _table.columns:
        if _col.name == "tenant_id" and _col.server_default is not None:
            _col.server_default = sa.schema.DefaultClause(sa.text("1"))


class _FakeSession:
    def execute(self, *_args, **_kwargs):
        return None

    def close(self) -> None:
        return None


def _override_get_db():
    yield _FakeSession()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
