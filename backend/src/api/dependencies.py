from collections.abc import AsyncGenerator
from typing import Annotated, Optional

import jwt
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.database import get_db, get_platform_db
from src.core.tenant_rls import arm, clear
from src.models.assinaturas import Assinatura
from src.models.platform_settings import PlatformSettings
from src.repositories import platform_admins_repository, revoked_tokens_repository
from src.services import billing_service

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_bearer)],
    db: Session = Depends(get_db),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente")
    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=["HS256"],
            options={"require": ["exp"]},
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
        ) from exc
    jti = payload.get("jti")
    if jti and revoked_tokens_repository.is_revoked(db, jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revogado")
    return payload


def check_subscription(
    db: Session = Depends(get_db),
    payload: dict = Depends(get_current_user),
) -> dict:
    """Block access for tenants with suspended/cancelled/expired subscriptions."""
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        return payload
    assinatura = db.execute(
        select(Assinatura).where(Assinatura.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if assinatura is None:
        return payload
    block = billing_service.evaluate_subscription_block(
        assinatura.status, assinatura.data_vencimento
    )
    if block is not None:
        setting = db.execute(
            select(PlatformSettings).where(PlatformSettings.key == "contact_email")
        ).scalar_one_or_none()
        contact = setting.value if setting else "contato@flow4tech.com.br"
        raise HTTPException(
            status_code=402,
            detail={"code": "SUBSCRIPTION_BLOCKED", "status": block["status"], "contact": contact},
        )
    return payload


async def get_tenant_db(
    db: Session = Depends(get_db),
    payload: dict = Depends(check_subscription),
) -> AsyncGenerator[Session, None]:
    """Session scoped to tenant via RLS (PostgreSQL only).

    Two-layer approach:
    1. arm() sets ROLE/tenant_id directly on this db session — necessary
       because get_current_user runs is_revoked() (a SQL query) before this
       function, which checks out the connection from the pool BEFORE
       _tenant_ctx is set. The checkout listener fires without tenant context.
       We must re-apply SET ROLE / SET tenant_id explicitly on the
       already-checked-out connection.
    2. arm() also sets _tenant_ctx (a contextvars.ContextVar, see
       core/tenant_rls.py) so the pool checkout listener re-establishes RLS
       context on any NEW connection checked out after db.commit()
       (SQLAlchemy 2.0 releases the connection on commit).

    This must stay `async def` (not a plain sync generator): FastAPI runs
    async generator dependencies' setup/teardown directly on the event loop,
    inside the request's own asyncio task, so the ContextVar.set() below
    mutates the task's own context. anyio's threadpool then copies that same
    (correctly mutated) task context into every later `run_in_threadpool`
    call for this request — including the endpoint body and any mid-request
    db.commit() that re-triggers the checkout listener. A sync generator
    dependency would instead run setup/teardown each in their own throwaway
    threadpool copy of the context, and the tenant_id set in setup would
    never be visible to the endpoint call or the listener.
    """
    tenant_id = payload.get("tenant_id")
    # Use session's bound engine — not the module-level engine — to detect dialect.
    # In unit tests, db may be bound to SQLite while DATABASE_URL / engine is PostgreSQL.
    _bind = getattr(db, "bind", None)
    _dialect = getattr(getattr(_bind, "dialect", None), "name", "")
    is_pg = tenant_id is not None and _dialect == "postgresql"
    if tenant_id is not None:
        structlog.contextvars.bind_contextvars(tenant_id=tenant_id)
    if is_pg:
        arm(db, tenant_id)
    try:
        yield db
    finally:
        if is_pg:
            clear(db)
        if tenant_id is not None:
            structlog.contextvars.unbind_contextvars("tenant_id")


def require_permission(screen: str):
    def _check(payload: dict = Depends(get_current_user)) -> dict:
        if "user_id" not in payload:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token sem user_id")
        permissions: list[str] = payload.get("permissions", [])
        if screen not in permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Sem permissão: {screen}")
        return payload

    return _check


def require_feature(feature_key: str):
    def _check(
        payload: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> dict:
        tenant_id = payload.get("tenant_id")
        if not tenant_id:
            return payload
        from src.models.tenant_features import TenantFeature
        row = db.execute(
            select(TenantFeature).where(
                TenantFeature.tenant_id == tenant_id,
                TenantFeature.feature == feature_key,
            )
        ).scalar_one_or_none()
        # Intentional opt-out semantics: tenant_features.enabled defaults to
        # TRUE at the DB level (see models/tenant_features.py) and
        # criar_tenant() does NOT seed rows for new tenants — every module
        # gated by require_feature() (comandas, financeiro, estoque, users,
        # dashboard, etc.) must work out of the box for a freshly created
        # tenant. A missing row therefore means "not explicitly restricted",
        # i.e. enabled. Only an explicit row with enabled=False (written via
        # upsert_tenant_features, e.g. to enforce a plan restriction) denies
        # access. Do not flip this to fail-closed: that would lock every new
        # tenant out of the entire application until a platform admin
        # manually seeds a row per feature.
        if row is not None and not row.enabled:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Módulo desabilitado: {feature_key}")
        return payload

    return _check


def require_platform_admin(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_bearer)],
    db: Session = Depends(get_platform_db),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente")
    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=["HS256"],
            options={"require": ["exp"]},
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
        ) from exc
    if not payload.get("platform_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a platform admins")
    if "tenant_id" in payload:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token de tenant não permitido aqui")
    jti = payload.get("jti")
    if jti and revoked_tokens_repository.is_revoked(db, jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revogado")
    admin_id = payload.get("platform_admin_id")
    if admin_id is not None:
        admin = platform_admins_repository.get_by_id(db, admin_id)
        if admin is None or not admin.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Conta desativada")
    return payload


__all__ = ["get_db", "get_tenant_db", "get_current_user", "check_subscription", "require_permission", "require_feature", "require_platform_admin"]  # noqa: E501
