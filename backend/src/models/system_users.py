from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.profiles import Profile


class SystemUser(Base):
    __tablename__ = "system_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(nullable=False, server_default="1")
    profile_id: Mapped[int] = mapped_column(sa.ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    username: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(sa.String(254), nullable=True)
    password_hash: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    last_login: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("NOW()"))

    profile: Mapped[Profile] = relationship(back_populates="users")
    password_resets: Mapped[list["PasswordReset"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(sa.ForeignKey("system_users.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(sa.String(100), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("NOW()"))

    user: Mapped[SystemUser] = relationship(back_populates="password_resets")
