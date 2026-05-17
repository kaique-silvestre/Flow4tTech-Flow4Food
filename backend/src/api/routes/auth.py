from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.schemas.auth import LoginRequest, TokenResponse, UserInfo
from src.services.auth_service import get_current_user_info, login

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
