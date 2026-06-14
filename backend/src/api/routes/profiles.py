from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_tenant_db, require_feature, require_permission
from src.schemas.permission_templates import AssignTemplateRequest
from src.schemas.profiles import ProfileCreate, ProfileResponse, ProfileUpdate
from src.services.profiles_service import (
    create_new_profile,
    delete_existing_profile,
    get_profile,
    get_profiles,
    toggle_profile_active,
    update_existing_profile,
)
from src.services.templates_service import assign_template_to_profile

router = APIRouter(dependencies=[Depends(require_feature("gestao_usuarios"))])


@router.get("", response_model=list[ProfileResponse])
def list_profiles(
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(require_permission("gestao_usuarios")),
) -> list[ProfileResponse]:
    return get_profiles(db, payload["tenant_id"])


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_one_profile(
    profile_id: int,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(require_permission("gestao_usuarios")),
) -> ProfileResponse:
    return get_profile(db, payload["tenant_id"], profile_id)


@router.post("", response_model=ProfileResponse, status_code=201)
def create_profile(
    body: ProfileCreate,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(require_permission("gestao_usuarios")),
) -> ProfileResponse:
    return create_new_profile(db, payload["tenant_id"], body)


@router.put("/{profile_id}", response_model=ProfileResponse)
def update_profile(
    profile_id: int,
    body: ProfileUpdate,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(require_permission("gestao_usuarios")),
) -> ProfileResponse:
    return update_existing_profile(db, payload["tenant_id"], profile_id, body)


@router.patch("/{profile_id}/activate", response_model=ProfileResponse)
def toggle_active(
    profile_id: int,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(require_permission("gestao_usuarios")),
) -> ProfileResponse:
    return toggle_profile_active(db, payload["tenant_id"], profile_id)


@router.patch("/{profile_id}/template", status_code=204)
def assign_profile_template(
    profile_id: int,
    body: AssignTemplateRequest,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(require_permission("gestao_usuarios")),
) -> None:
    assign_template_to_profile(db, payload["tenant_id"], profile_id, body)


@router.delete("/{profile_id}", status_code=204)
def delete_profile(
    profile_id: int,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(require_permission("gestao_usuarios")),
) -> None:
    delete_existing_profile(db, payload["tenant_id"], profile_id)
