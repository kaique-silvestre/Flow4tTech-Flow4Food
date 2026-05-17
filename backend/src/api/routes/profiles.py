from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_db, require_permission
from src.schemas.profiles import ProfileCreate, ProfileResponse, ProfileUpdate
from src.services.profiles_service import (
    create_new_profile,
    delete_existing_profile,
    get_profile,
    get_profiles,
    toggle_profile_active,
    update_existing_profile,
)

router = APIRouter()

_perm = Depends(require_permission("gestao_usuarios"))


@router.get("", response_model=list[ProfileResponse], dependencies=[_perm])
def list_profiles(db: Session = Depends(get_db)) -> list[ProfileResponse]:
    return get_profiles(db)


@router.get("/{profile_id}", response_model=ProfileResponse, dependencies=[_perm])
def get_one_profile(profile_id: int, db: Session = Depends(get_db)) -> ProfileResponse:
    return get_profile(db, profile_id)


@router.post("", response_model=ProfileResponse, status_code=201, dependencies=[_perm])
def create_profile(body: ProfileCreate, db: Session = Depends(get_db)) -> ProfileResponse:
    return create_new_profile(db, body)


@router.put("/{profile_id}", response_model=ProfileResponse, dependencies=[_perm])
def update_profile(profile_id: int, body: ProfileUpdate, db: Session = Depends(get_db)) -> ProfileResponse:
    return update_existing_profile(db, profile_id, body)


@router.patch("/{profile_id}/activate", response_model=ProfileResponse, dependencies=[_perm])
def toggle_active(profile_id: int, db: Session = Depends(get_db)) -> ProfileResponse:
    return toggle_profile_active(db, profile_id)


@router.delete("/{profile_id}", status_code=204, dependencies=[_perm])
def delete_profile(profile_id: int, db: Session = Depends(get_db)) -> None:
    delete_existing_profile(db, profile_id)
