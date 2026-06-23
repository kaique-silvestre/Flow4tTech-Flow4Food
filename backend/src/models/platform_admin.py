from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class PlatformAdmin(Base):
    __tablename__ = "platform_admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(sa.String(254), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    password_hash: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    created_at: Mapped[Optional[datetime]] = mapped_column(  # noqa: UP045
        sa.DateTime(timezone=True), server_default=sa.text("NOW()")
    )
