from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_db, require_permission
from src.schemas.users import (
    ResetPasswordResponse,
    UserCreate,
    UsernameCheckResponse,
    UserResponse,
    UserUpdate,
)
from src.services.users_service import (
    check_email_available,
    check_username_available,
    create_new_user,
    delete_existing_user,
    get_user,
    get_users,
    reset_password,
    toggle_user_active,
    update_existing_user,
)

router = APIRouter()

_perm = Depends(require_permission("gestao_usuarios"))


@router.get("", response_model=list[UserResponse], dependencies=[_perm])
def list_users(
    search: Optional[str] = Query(None),
    profile_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> list[UserResponse]:
    return get_users(db, search, profile_id)


@router.post("", response_model=UserResponse, status_code=201, dependencies=[_perm])
def create_user(body: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    return create_new_user(db, body)


@router.get("/check-username", response_model=UsernameCheckResponse)
def check_username(username: str = Query(...), db: Session = Depends(get_db)) -> UsernameCheckResponse:
    return UsernameCheckResponse(available=check_username_available(db, username))


@router.get("/check-email", response_model=UsernameCheckResponse)
def check_email(email: str = Query(...), db: Session = Depends(get_db)) -> UsernameCheckResponse:
    return UsernameCheckResponse(available=check_email_available(db, email))


@router.get("/{user_id}", response_model=UserResponse, dependencies=[_perm])
def get_one_user(user_id: int, db: Session = Depends(get_db)) -> UserResponse:
    return get_user(db, user_id)


@router.put("/{user_id}", response_model=UserResponse, dependencies=[_perm])
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(require_permission("gestao_usuarios")),
) -> UserResponse:
    current_user_id: int = payload["user_id"]
    return update_existing_user(db, user_id, body, current_user_id)


@router.delete("/{user_id}", status_code=204, dependencies=[_perm])
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(require_permission("gestao_usuarios")),
) -> None:
    current_user_id: int = payload["user_id"]
    delete_existing_user(db, user_id, current_user_id)


@router.patch("/{user_id}/activate", response_model=UserResponse, dependencies=[_perm])
def toggle_active(
    user_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(require_permission("gestao_usuarios")),
) -> UserResponse:
    current_user_id: int = payload["user_id"]
    return toggle_user_active(db, user_id, current_user_id)


@router.post("/{user_id}/reset-password", response_model=ResetPasswordResponse, dependencies=[_perm])
def do_reset_password(user_id: int, db: Session = Depends(get_db)) -> ResetPasswordResponse:
    temp = reset_password(db, user_id)
    return ResetPasswordResponse(temp_password=temp)
