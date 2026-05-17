from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.system_users import SystemUser


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(nullable=False, server_default="1")
    name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.String(300), nullable=True)
    is_system: Mapped[bool] = mapped_column(nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("NOW()"))

    permissions: Mapped[list[ProfilePermission]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    users: Mapped[list[SystemUser]] = relationship(back_populates="profile")


class ProfilePermission(Base):
    __tablename__ = "profile_permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    screen: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    can_access: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("NOW()"))

    profile: Mapped[Profile] = relationship(back_populates="permissions")
