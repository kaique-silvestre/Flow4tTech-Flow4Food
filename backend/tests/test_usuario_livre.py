"""Tests for issue #18 — free user (profile_id nullable + user_permissions)."""

import os
from datetime import datetime, timezone

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

import jwt
import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.core.database import Base
from src.models.system_users import SystemUser
from src.models.user_permissions import UserPermission
from src.services.auth_service import (
    create_refresh_token,
    hash_password,
    resolve_permissions,
    rotate_refresh_token,
)

_JWT_SECRET = "test-secret-only-for-tests-32chars!!"
_engine = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
_Session = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


def _free_user(db, user_id: int, now) -> SystemUser:
    user = SystemUser(
        id=user_id,
        tenant_id=1,
        profile_id=None,
        name="Free User",
        username=f"freeuser{user_id}",
        password_hash=hash_password("pass"),
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    return user


# G1: free user without any user_permissions → permissions = []
def test_resolve_permissions_free_user_no_permissions():
    db = _Session()
    try:
        now = datetime.now(timezone.utc)
        user = _free_user(db, 10, now)
        db.expire_all()
        db.refresh(user)
        perms = resolve_permissions(user)
        assert perms == []
    finally:
        db.close()


# G2: free user with user_permissions → JWT contains those screens
def test_resolve_permissions_free_user_with_permissions():
    db = _Session()
    try:
        now = datetime.now(timezone.utc)
        user = _free_user(db, 11, now)
        db.add(UserPermission(tenant_id=1, user_id=11, screen="vendas", can_access=True))
        db.add(UserPermission(tenant_id=1, user_id=11, screen="cozinha", can_access=True))
        db.commit()
        db.expire_all()
        db.refresh(user)
        _ = user.user_permissions  # ensure loaded
        perms = resolve_permissions(user)
        assert set(perms) == {"vendas", "cozinha"}
    finally:
        db.close()


# G3: free user with can_access=False entries excluded
def test_resolve_permissions_free_user_can_access_false_excluded():
    db = _Session()
    try:
        now = datetime.now(timezone.utc)
        user = _free_user(db, 12, now)
        db.add(UserPermission(tenant_id=1, user_id=12, screen="vendas", can_access=True))
        db.add(UserPermission(tenant_id=1, user_id=12, screen="relatorios", can_access=False))
        db.commit()
        db.expire_all()
        db.refresh(user)
        _ = user.user_permissions
        perms = resolve_permissions(user)
        assert perms == ["vendas"]
    finally:
        db.close()


# G4: rotate_refresh_token with free user → no crash, permissions=[] if no user_permissions
def test_rotate_refresh_token_free_user_no_crash(monkeypatch):
    import src.services.auth_service as auth_svc
    monkeypatch.setattr(auth_svc, "get_assinatura_by_tenant", lambda db, tid: None)

    db = _Session()
    try:
        now = datetime.now(timezone.utc)
        user = _free_user(db, 20, now)
        raw_refresh = create_refresh_token(db, user.id)
        db.expire_all()
        new_access, _ = rotate_refresh_token(db, raw_refresh)
        payload = jwt.decode(new_access, _JWT_SECRET, algorithms=["HS256"])
        assert payload["permissions"] == []
        assert payload["profile_id"] is None
        assert payload["profile_name"] is None
    finally:
        db.close()


# G5: rotate_refresh_token with free user with user_permissions → JWT has screens
def test_rotate_refresh_token_free_user_with_permissions(monkeypatch):
    import src.services.auth_service as auth_svc
    monkeypatch.setattr(auth_svc, "get_assinatura_by_tenant", lambda db, tid: None)

    db = _Session()
    try:
        now = datetime.now(timezone.utc)
        user = _free_user(db, 21, now)
        db.add(UserPermission(tenant_id=1, user_id=21, screen="gestao_usuarios", can_access=True))
        db.commit()
        raw_refresh = create_refresh_token(db, user.id)
        db.expire_all()
        new_access, _ = rotate_refresh_token(db, raw_refresh)
        payload = jwt.decode(new_access, _JWT_SECRET, algorithms=["HS256"])
        assert payload["permissions"] == ["gestao_usuarios"]
    finally:
        db.close()
