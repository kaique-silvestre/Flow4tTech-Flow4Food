from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_tenant_db, require_permission
from src.schemas.permission_templates import (
    TemplateCreate,
    TemplateResponse,
    TemplateUpdate,
)
from src.services.templates_service import (
    create_new_template,
    delete_existing_template,
    get_templates,
    update_existing_template,
)

router = APIRouter()


@router.get("", response_model=list[TemplateResponse])
def list_permission_templates(
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(require_permission("gestao_usuarios")),
) -> list[TemplateResponse]:
    return get_templates(db, payload["tenant_id"])


@router.post("", response_model=TemplateResponse, status_code=201)
def create_permission_template(
    body: TemplateCreate,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(require_permission("gestao_usuarios")),
) -> TemplateResponse:
    return create_new_template(db, payload["tenant_id"], body)


@router.patch("/{template_id}", response_model=TemplateResponse)
def update_permission_template(
    template_id: int,
    body: TemplateUpdate,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(require_permission("gestao_usuarios")),
) -> TemplateResponse:
    return update_existing_template(db, payload["tenant_id"], template_id, body)


@router.delete("/{template_id}", status_code=204)
def delete_permission_template(
    template_id: int,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(require_permission("gestao_usuarios")),
) -> None:
    delete_existing_template(db, payload["tenant_id"], template_id)
