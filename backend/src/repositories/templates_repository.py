from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from src.models.profiles import PermissionTemplate, Profile, TemplatePermission


def _with_perms(q):
    return q.options(joinedload(PermissionTemplate.permissions))


def list_templates(db: Session, tenant_id: int) -> list[PermissionTemplate]:
    """Templates de sistema (tenant_id NULL) + custom do tenant."""
    return (
        _with_perms(db.query(PermissionTemplate))
        .filter(
            or_(
                PermissionTemplate.is_system.is_(True),
                PermissionTemplate.tenant_id == tenant_id,
            )
        )
        .order_by(PermissionTemplate.is_system.desc(), PermissionTemplate.nome)
        .all()
    )


def get_template_by_id(db: Session, template_id: int) -> Optional[PermissionTemplate]:
    return _with_perms(
        db.query(PermissionTemplate).filter(PermissionTemplate.id == template_id)
    ).first()


def create_template(
    db: Session, tenant_id: int, nome: str, descricao: Optional[str], screens: list[str]
) -> PermissionTemplate:
    template = PermissionTemplate(
        tenant_id=tenant_id, nome=nome, descricao=descricao, is_system=False
    )
    db.add(template)
    db.flush()
    for screen in screens:
        db.add(TemplatePermission(template_id=template.id, screen=screen, can_access=True))
    db.commit()
    return get_template_by_id(db, template.id)  # type: ignore[return-value]


def update_template(
    db: Session,
    template: PermissionTemplate,
    nome: Optional[str],
    descricao: Optional[str],
    screens: Optional[list[str]],
) -> PermissionTemplate:
    if nome is not None:
        template.nome = nome
    if descricao is not None:
        template.descricao = descricao
    if screens is not None:
        db.query(TemplatePermission).filter(
            TemplatePermission.template_id == template.id
        ).delete()
        for screen in screens:
            db.add(TemplatePermission(template_id=template.id, screen=screen, can_access=True))
    db.commit()
    return get_template_by_id(db, template.id)  # type: ignore[return-value]


def delete_template(db: Session, template: PermissionTemplate) -> None:
    db.delete(template)
    db.commit()


def get_template_screens(db: Session, template_id: int) -> list[str]:
    rows = (
        db.query(TemplatePermission.screen)
        .filter(
            TemplatePermission.template_id == template_id,
            TemplatePermission.can_access.is_(True),
        )
        .all()
    )
    return [r[0] for r in rows]


def assign_template(
    db: Session, profile: Profile, template_id: Optional[int]
) -> Profile:
    profile.template_id = template_id
    db.commit()
    db.refresh(profile)
    return profile
