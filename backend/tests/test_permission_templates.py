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
from src.models.profiles import PermissionTemplate, Profile, TemplatePermission

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSession = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def _fake_user() -> dict:
    return {
        "sub": "1",
        "user_id": 1,
        "tenant_id": 1,
        "permissions": ["gestao_usuarios"],
    }


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


@pytest.fixture
def client():
    def override_get_db():
        db = _TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _fake_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _seed_profile(name: str = "Caixa", is_system: bool = True) -> int:
    db = _TestingSession()
    now = datetime.now(timezone.utc)
    p = Profile(
        tenant_id=1, name=name, description="d", is_system=is_system,
        created_at=now, updated_at=now,
    )
    db.add(p)
    db.commit()
    pid = p.id
    db.close()
    return pid


def _seed_system_template(nome: str = "Sys") -> int:
    db = _TestingSession()
    t = PermissionTemplate(tenant_id=None, nome=nome, descricao="d", is_system=True)
    db.add(t)
    db.flush()
    db.add(TemplatePermission(template_id=t.id, screen="dashboard", can_access=True))
    db.commit()
    tid = t.id
    db.close()
    return tid


# F1 — criar template → associar a perfil → confirmar profile.template_id
def test_create_template_and_assign_to_profile(client):
    profile_id = _seed_profile()

    resp = client.post(
        "/api/permission-templates",
        json={"nome": "Custom", "descricao": "x", "screens": ["dashboard", "comandas"]},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    template_id = body["id"]
    assert body["is_system"] is False
    assert sorted(body["screens"]) == ["comandas", "dashboard"]

    assign = client.patch(
        f"/api/profiles/{profile_id}/template", json={"template_id": template_id}
    )
    assert assign.status_code == 204, assign.text

    db = _TestingSession()
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    assert profile.template_id == template_id
    db.close()


def test_list_includes_system_and_custom(client):
    _seed_system_template("SysA")
    client.post(
        "/api/permission-templates",
        json={"nome": "CustomB", "screens": ["dashboard"]},
    )
    resp = client.get("/api/permission-templates")
    assert resp.status_code == 200
    nomes = {t["nome"] for t in resp.json()}
    assert {"SysA", "CustomB"} <= nomes


# F2 — deletar template is_system=True deve falhar
def test_delete_system_template_blocked(client):
    template_id = _seed_system_template()
    resp = client.delete(f"/api/permission-templates/{template_id}")
    assert resp.status_code == 409, resp.text


def test_unassign_template_sets_null(client):
    profile_id = _seed_profile()
    template_id = _seed_system_template()
    client.patch(f"/api/profiles/{profile_id}/template", json={"template_id": template_id})
    resp = client.patch(f"/api/profiles/{profile_id}/template", json={"template_id": None})
    assert resp.status_code == 204

    db = _TestingSession()
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    assert profile.template_id is None
    db.close()


# F3 — migration reversível (metadata smoke: tabelas existem e dropam limpo)
def test_template_tables_roundtrip():
    assert "permission_templates" in Base.metadata.tables
    assert "template_permissions" in Base.metadata.tables
    Base.metadata.create_all(_engine)
    Base.metadata.drop_all(_engine)
