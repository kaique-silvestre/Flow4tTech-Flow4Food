from collections.abc import Generator
from datetime import timezone
from typing import Annotated, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.database import _tenant_ctx, get_db, get_platform_db  # noqa: F401
from src.models.assinaturas import Assinatura
from src.models.platform_settings import PlatformSettings
from src.repositories import platform_admins_repository, revoked_tokens_repository

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_bearer)],
    db: Session = Depends(get_db),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente")
    settings = get_settings()
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"])
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
    from datetime import datetime
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        return payload
    assinatura = db.execute(
        select(Assinatura).where(Assinatura.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if assinatura is None:
        return payload
    now = datetime.now(timezone.utc)
    dv = assinatura.data_vencimento
    if dv is not None and dv.tzinfo is None:
        dv = dv.replace(tzinfo=timezone.utc)
    trial_expired = assinatura.status == "trial" and dv is not None and dv < now
    if assinatura.status in {"suspensa", "cancelada"} or trial_expired:
        setting = db.execute(
            select(PlatformSettings).where(PlatformSettings.key == "contact_email")
        ).scalar_one_or_none()
        contact = setting.value if setting else "contato@flow4tech.com.br"
        raise HTTPException(
            status_code=402,
            detail={"code": "SUBSCRIPTION_BLOCKED", "status": assinatura.status, "contact": contact},
        )
    return payload


def get_tenant_db(
    db: Session = Depends(get_db),
    payload: dict = Depends(check_subscription),
) -> Generator[Session, None, None]:
    """Session scoped to tenant via RLS (PostgreSQL only).

    Two-layer approach:
    1. Direct SET on db session here — necessary because get_current_user runs
       is_revoked() (a SQL query) before this function, which checks out the
       connection from the pool BEFORE _tenant_ctx is set. The checkout listener
       fires without tenant context. We must re-apply SET ROLE / SET tenant_id
       explicitly on the already-checked-out connection.
    2. _tenant_ctx (thread-local) is set so the pool checkout listener
       re-establishes RLS context on any NEW connection checked out after
       db.commit() (SQLAlchemy 2.0 releases connection on commit).
    """
    tenant_id = payload.get("tenant_id")
    # Use session's bound engine — not the module-level engine — to detect dialect.
    # In unit tests, db may be bound to SQLite while DATABASE_URL / engine is PostgreSQL.
    _bind = getattr(db, "bind", None)
    _dialect = getattr(getattr(_bind, "dialect", None), "name", "")
    is_pg = tenant_id is not None and _dialect == "postgresql"
    if is_pg:
        _tenant_ctx.tenant_id = tenant_id
        db.execute(text("SET ROLE app_user"))
        db.execute(text("SET app.tenant_id = :tid"), {"tid": str(tenant_id)})
    try:
        yield db
    finally:
        if is_pg:
            _tenant_ctx.tenant_id = None


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
        if row is not None and not row.enabled:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Módulo desabilitado: {feature_key}")
        return payload

    return _check


def require_active_subscription(payload: dict = Depends(get_current_user)) -> dict:
    sub_status = payload.get("subscription_status", "trial")
    if sub_status not in {"ativa", "trial"}:
        raise HTTPException(status_code=402, detail="Assinatura vencida ou suspensa")
    return payload


def require_platform_admin(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_bearer)],
    db: Session = Depends(get_platform_db),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente")
    settings = get_settings()
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"])
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


__all__ = ["get_db", "get_tenant_db", "get_current_user", "check_subscription", "require_permission", "require_feature", "require_active_subscription", "require_platform_admin"]  # noqa: E501
