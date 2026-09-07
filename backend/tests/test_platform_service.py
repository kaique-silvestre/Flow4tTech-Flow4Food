import os
from datetime import datetime, timezone

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.core.database import Base
from src.models.profiles import Profile, ProfilePermission
from src.models.system_users import SystemUser
from src.models.tenants import Tenant
from src.models.user_permissions import UserPermission
from src.services import platform_service
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
def db():
    session = _Session()
    try:
        yield session
    finally:
        session.close()


def _seed_tenant(db) -> Tenant:
    now = datetime.now(timezone.utc)
    t = Tenant(nome_fantasia="Empresa Teste", status="ativo", max_users=5, created_at=now)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def _seed_user(db, tenant_id: int, profile_id: int = None) -> SystemUser:
    now = datetime.now(timezone.utc)
    u = SystemUser(
        tenant_id=tenant_id,
        name="Usuário Teste",
        username="usuario_teste",
        email="user@teste.com",
        password_hash=hash_password("senha123"),
        profile_id=profile_id,
        created_at=now,
        updated_at=now,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def test_resolve_impersonation_permissions_uses_explicit_grants(db):
    tenant = _seed_tenant(db)
    user = _seed_user(db, tenant.id)
    db.add(UserPermission(tenant_id=tenant.id, user_id=user.id, screen="caixa"))
    db.add(UserPermission(tenant_id=tenant.id, user_id=user.id, screen="dashboard"))
    db.commit()

    perms = platform_service.resolve_impersonation_permissions(db, user)

    assert sorted(perms) == ["caixa", "dashboard"]


def test_resolve_impersonation_permissions_falls_back_to_profile(db):
    tenant = _seed_tenant(db)
    now = datetime.now(timezone.utc)
    profile = Profile(tenant_id=tenant.id, name="Admin", created_at=now, updated_at=now)
    db.add(profile)
    db.flush()
    db.add(
        ProfilePermission(
            tenant_id=tenant.id, profile_id=profile.id, screen="relatorios", created_at=now
        )
    )
    db.commit()
    user = _seed_user(db, tenant.id, profile_id=profile.id)

    perms = platform_service.resolve_impersonation_permissions(db, user)

    assert perms == ["relatorios"]


def test_resolve_impersonation_permissions_no_grants_no_profile_is_empty(db):
    tenant = _seed_tenant(db)
    user = _seed_user(db, tenant.id)

    perms = platform_service.resolve_impersonation_permissions(db, user)

    assert perms == []
