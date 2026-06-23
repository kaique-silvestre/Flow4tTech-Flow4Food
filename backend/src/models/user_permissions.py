from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.system_users import SystemUser


class UserPermission(Base):
    __tablename__ = "user_permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        sa.BigInteger(),
        nullable=False,
        server_default=sa.text("(NULLIF(current_setting('app.tenant_id', true), ''))::bigint"),
    )
    user_id: Mapped[int] = mapped_column(
        sa.ForeignKey("system_users.id", ondelete="CASCADE"), nullable=False
    )
    screen: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    can_access: Mapped[bool] = mapped_column(nullable=False, server_default="true")

    user: Mapped[SystemUser] = relationship(back_populates="user_permissions")
