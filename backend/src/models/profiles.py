from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.system_users import SystemUser


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False, server_default=sa.text("(NULLIF(current_setting('app.tenant_id', true), ''))::bigint"))
    name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(sa.String(300), nullable=True)  # noqa: UP045 — str|None breaks SQLAlchemy on Python 3.9
    is_system: Mapped[bool] = mapped_column(nullable=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    template_id: Mapped[Optional[int]] = mapped_column(  # noqa: UP045 — int|None breaks SQLAlchemy on Python 3.9
        sa.ForeignKey("permission_templates.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("NOW()"))

    permissions: Mapped[list[ProfilePermission]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    users: Mapped[list[SystemUser]] = relationship(back_populates="profile")
    template: Mapped[Optional[PermissionTemplate]] = relationship(back_populates="profiles")  # noqa: UP045


class ProfilePermission(Base):
    __tablename__ = "profile_permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False, server_default=sa.text("(NULLIF(current_setting('app.tenant_id', true), ''))::bigint"))
    profile_id: Mapped[int] = mapped_column(sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    screen: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    can_access: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("NOW()"))

    profile: Mapped[Profile] = relationship(back_populates="permissions")


class PermissionTemplate(Base):
    __tablename__ = "permission_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(  # noqa: UP045 — int|None breaks SQLAlchemy on Python 3.9
        sa.BigInteger(), nullable=True,
        server_default=sa.text("(NULLIF(current_setting('app.tenant_id', true), ''))::bigint"),
    )
    nome: Mapped[str] = mapped_column(sa.String(60), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(sa.String(200), nullable=True)  # noqa: UP045
    is_system: Mapped[bool] = mapped_column(nullable=False, server_default="false")

    permissions: Mapped[list[TemplatePermission]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )
    profiles: Mapped[list[Profile]] = relationship(back_populates="template")


class TemplatePermission(Base):
    __tablename__ = "template_permissions"

    template_id: Mapped[int] = mapped_column(
        sa.ForeignKey("permission_templates.id", ondelete="CASCADE"), primary_key=True
    )
    screen: Mapped[str] = mapped_column(sa.String(50), primary_key=True)
    can_access: Mapped[bool] = mapped_column(nullable=False, server_default="true")

    template: Mapped[PermissionTemplate] = relationship(back_populates="permissions")
