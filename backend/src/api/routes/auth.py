from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.core.config import get_settings
from src.core.errors import AppError
from src.core.limiter import limiter
from src.repositories import revoked_tokens_repository
from src.schemas.auth import (
    AccessTokenResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    GenericMessage,
    LoginRequest,
    ResetPasswordRequest,
    ResetTokenInfo,
    TokenResponse,
    UserInfo,
)
from src.services import audit_service
from src.services.auth_service import (
    change_password,
    create_refresh_token,
    forgot_password,
    get_current_user_info,
    get_reset_token_info,
    login,
    reset_password,
    revoke_all_refresh_tokens,
    rotate_refresh_token,
)

router = APIRouter()

_COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=settings.REFRESH_TOKEN_EXPIRES_DAYS * 86400,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/15minutes")
def do_login(
    request: Request,
    body: LoginRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> TokenResponse:
    try:
        token_response = login(db, body.identifier, body.password)
    except AppError:
        background_tasks.add_task(
            audit_service.log_background,
            "auth.login_failed",
            after={"identifier": body.identifier},
        )
        raise
    token_payload = _decode_token(token_response.access_token)
    user_id = token_payload.get("user_id") if token_payload else None
    tenant_id = token_payload.get("tenant_id") if token_payload else None
    background_tasks.add_task(
        audit_service.log_background,
        "auth.login_success",
        tenant_id=tenant_id,
        user_id=user_id,
    )
    if user_id is not None:
        raw_refresh = create_refresh_token(db, user_id)
        _set_refresh_cookie(response, raw_refresh)
    return token_response


def _decode_token(access_token: str) -> Optional[dict]:
    import jwt as _jwt

    try:
        settings = get_settings()
        return _jwt.decode(
            access_token, settings.JWT_SECRET, algorithms=["HS256"], options={"require": ["exp"]}
        )
    except Exception:
        return None


@router.post("/refresh", response_model=AccessTokenResponse)
def do_refresh(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: Optional[str] = Cookie(default=None),
) -> AccessTokenResponse:
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token ausente")
    new_access, new_refresh = rotate_refresh_token(db, refresh_token)
    _set_refresh_cookie(response, new_refresh)
    return AccessTokenResponse(access_token=new_access)


@router.post("/logout", status_code=204)
def do_logout(
    response: Response,
    background_tasks: BackgroundTasks,
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    jti = payload.get("jti")
    exp_ts = payload.get("exp")
    if jti and exp_ts:
        expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
        revoked_tokens_repository.revoke(db, jti, expires_at)
    user_id = payload.get("user_id")
    if user_id:
        revoke_all_refresh_tokens(db, user_id)
    response.delete_cookie(_COOKIE_NAME, samesite="none", secure=True)
    background_tasks.add_task(
        audit_service.log_background,
        "auth.logout",
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
    )
    return None


@router.get("/me", response_model=UserInfo)
def me(payload: dict = Depends(get_current_user)) -> UserInfo:
    return get_current_user_info(payload)


@router.post("/change-password", status_code=204)
def do_change_password(
    body: ChangePasswordRequest,
    background_tasks: BackgroundTasks,
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    change_password(db, payload["user_id"], body.current_password, body.new_password)
    background_tasks.add_task(
        audit_service.log_background,
        "auth.password_changed",
        tenant_id=payload.get("tenant_id"),
        user_id=payload["user_id"],
    )


@router.post("/forgot-password", response_model=GenericMessage)
def do_forgot_password(
    body: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> GenericMessage:
    result = forgot_password(db, body.email)
    background_tasks.add_task(
        audit_service.log_background,
        "auth.password_reset_requested",
        after={"email": body.email},
    )
    return result


@router.get("/reset-password/{token}", response_model=ResetTokenInfo)
@limiter.limit("5/15minutes")
def get_reset_info(request: Request, token: str, db: Session = Depends(get_db)) -> ResetTokenInfo:
    return get_reset_token_info(db, token)


@router.post("/reset-password", status_code=204)
def do_reset_password(
    body: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> None:
    user_id = reset_password(db, body.token, body.new_password)
    background_tasks.add_task(
        audit_service.log_background,
        "auth.password_reset_completed",
        user_id=user_id,
    )
