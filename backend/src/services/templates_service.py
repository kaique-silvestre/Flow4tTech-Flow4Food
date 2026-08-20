from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.profiles import PermissionTemplate
from src.repositories.profiles_repository import get_profile_by_id
from src.repositories.templates_repository import (
    assign_template,
    create_template,
    delete_template,
    get_template_by_id,
    list_templates,
    update_template,
)
from src.schemas.permission_templates import (
    AssignTemplateRequest,
    TemplateCreate,
    TemplateResponse,
    TemplateUpdate,
)


def _to_response(template: PermissionTemplate) -> TemplateResponse:
    return TemplateResponse(
        id=template.id,
        tenant_id=template.tenant_id,
        nome=template.nome,
        descricao=template.descricao,
        is_system=template.is_system,
        screens=[p.screen for p in template.permissions if p.can_access],
    )


def _get_owned(db: Session, tenant_id: int, template_id: int) -> PermissionTemplate:
    template = get_template_by_id(db, template_id, tenant_id)
    visible = template and (template.is_system or template.tenant_id == tenant_id)
    if not template or not visible:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Template não encontrado", http_status=404)
    return template


def get_templates(db: Session, tenant_id: int) -> list[TemplateResponse]:
    return [_to_response(t) for t in list_templates(db, tenant_id)]


def create_new_template(db: Session, tenant_id: int, data: TemplateCreate) -> TemplateResponse:
    template = create_template(db, tenant_id, data.nome, data.descricao, data.screens)
    return _to_response(template)


def update_existing_template(
    db: Session, tenant_id: int, template_id: int, data: TemplateUpdate
) -> TemplateResponse:
    template = _get_owned(db, tenant_id, template_id)
    if template.is_system:
        raise AppError(
            code=ErrorCode.CONFLICT,
            message="Templates de sistema não podem ser alterados",
            http_status=409,
        )
    return _to_response(update_template(db, template, data.nome, data.descricao, data.screens))


def delete_existing_template(db: Session, tenant_id: int, template_id: int) -> None:
    template = _get_owned(db, tenant_id, template_id)
    if template.is_system:
        raise AppError(
            code=ErrorCode.CONFLICT,
            message="Templates de sistema não podem ser excluídos",
            http_status=409,
        )
    delete_template(db, template)


def assign_template_to_profile(
    db: Session, tenant_id: int, profile_id: int, data: AssignTemplateRequest
) -> None:
    profile = get_profile_by_id(db, profile_id)
    if not profile or profile.tenant_id != tenant_id:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Perfil não encontrado", http_status=404)
    if data.template_id is not None:
        _get_owned(db, tenant_id, data.template_id)
    assign_template(db, profile, data.template_id)
