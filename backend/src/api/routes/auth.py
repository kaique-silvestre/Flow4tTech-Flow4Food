from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    GenericMessage,
    LoginRequest,
    ResetPasswordRequest,
    ResetTokenInfo,
    TokenResponse,
    UserInfo,
)
from src.services.auth_service import (
    change_password,
    forgot_password,
    get_current_user_info,
    get_reset_token_info,
    login,
    reset_password,
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def do_login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return login(db, body.identifier, body.password)


@router.post("/logout", status_code=204)
def do_logout() -> None:
    return None


@router.get("/me", response_model=UserInfo)
def me(payload: dict = Depends(get_current_user)) -> UserInfo:
    return get_current_user_info(payload)


@router.post("/change-password", status_code=204)
def do_change_password(
    body: ChangePasswordRequest,
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    change_password(db, payload["user_id"], body.current_password, body.new_password)


@router.post("/forgot-password", response_model=GenericMessage)
def do_forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)) -> GenericMessage:
    return forgot_password(db, body.email)


@router.get("/reset-password/{token}", response_model=ResetTokenInfo)
def get_reset_info(token: str, db: Session = Depends(get_db)) -> ResetTokenInfo:
    return get_reset_token_info(db, token)


@router.post("/reset-password", status_code=204)
def do_reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)) -> None:
    reset_password(db, body.token, body.new_password)
