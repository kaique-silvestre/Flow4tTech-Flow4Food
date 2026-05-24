import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests")
os.environ.setdefault("ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_current_user, get_db
from src.core.database import Base
from src.main import app
from src.models.auth import ConfigSeguranca
from src.services.auth_service import hash_password, verify_password

_SQLITE_URL = "sqlite:///:memory:"
_engine = create_engine(
    _SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSession = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def _fake_user() -> dict:
    return {"sub": "1", "user_id": 1, "tenant_id": 1, "permissions": ["cadastros", "comandas", "compras", "configuracoes", "dashboard", "estoque", "gestao_usuarios", "relatorios"]}


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


@pytest.fixture
def c():
    def override_get_db():
        db = _TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _fake_user
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_get_estabelecimento_defaults(c: TestClient) -> None:
    r = c.get("/api/config/estabelecimento")
    assert r.status_code == 200
    data = r.json()
    assert data["nome"] == "Estabelecimento"
    assert data["cnpj"] is None
    assert data["endereco"] is None
    assert data["telefone"] is None


def test_patch_estabelecimento(c: TestClient) -> None:
    r = c.patch(
        "/api/config/estabelecimento",
        json={"nome": "Bar do Ze", "telefone": "11999998888"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["nome"] == "Bar do Ze"
    assert data["telefone"] == "11999998888"
    assert data["cnpj"] is None


def test_alterar_senha_senha_incorreta(c: TestClient) -> None:
    db = _TestingSession()
    config = ConfigSeguranca(senha_hash=hash_password("senha123"))
    db.add(config)
    db.commit()
    db.close()

    r = c.patch("/api/config/senha", json={"senha_atual": "errada", "nova_senha": "nova456"})
    assert r.status_code == 401


def test_alterar_senha_sucesso(c: TestClient) -> None:
    db = _TestingSession()
    config = ConfigSeguranca(senha_hash=hash_password("senha123"))
    db.add(config)
    db.commit()
    db.close()

    r = c.patch("/api/config/senha", json={"senha_atual": "senha123", "nova_senha": "nova456"})
    assert r.status_code == 204

    db2 = _TestingSession()
    from src.repositories.auth_repository import get_config
    updated = get_config(db2)
    assert updated is not None
    assert verify_password("nova456", updated.senha_hash)
    db2.close()


def test_backup_json(c: TestClient) -> None:
    r = c.get("/api/backup?formato=json")
    assert r.status_code == 200
    assert "application/json" in r.headers["content-type"]
    data = r.json()
    assert "estabelecimento" in data


def test_backup_xlsx(c: TestClient) -> None:
    r = c.get("/api/backup?formato=xlsx")
    assert r.status_code == 200
    assert "spreadsheetml" in r.headers["content-type"]
    assert len(r.content) > 0
