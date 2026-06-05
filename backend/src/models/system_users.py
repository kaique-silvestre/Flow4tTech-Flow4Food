from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.profiles import Profile

if TYPE_CHECKING:
    from src.models.refresh_tokens import RefreshToken


class SystemUser(Base):
    __tablename__ = "system_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False, server_default=sa.text("(NULLIF(current_setting('app.tenant_id', true), ''))::bigint"))
    profile_id: Mapped[int] = mapped_column(sa.ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    username: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(sa.String(254), nullable=True)  # noqa: UP045
    password_hash: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    last_login: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)  # noqa: UP045
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("NOW()"))

    profile: Mapped[Profile] = relationship(back_populates="users")
    password_resets: Mapped[list[PasswordReset]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(sa.ForeignKey("system_users.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(sa.String(100), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)  # noqa: UP045
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("NOW()"))

    user: Mapped[SystemUser] = relationship(back_populates="password_resets")
