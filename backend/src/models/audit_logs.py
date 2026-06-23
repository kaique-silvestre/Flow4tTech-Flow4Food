from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(sa.Integer(), nullable=True)  # noqa: UP045
    user_id: Mapped[Optional[int]] = mapped_column(sa.Integer(), nullable=True)  # noqa: UP045
    action: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    entity: Mapped[Optional[str]] = mapped_column(sa.String(100), nullable=True)  # noqa: UP045
    entity_id: Mapped[Optional[int]] = mapped_column(sa.Integer(), nullable=True)  # noqa: UP045
    before_data: Mapped[Optional[str]] = mapped_column(sa.Text(), nullable=True)  # noqa: UP045
    after_data: Mapped[Optional[str]] = mapped_column(sa.Text(), nullable=True)  # noqa: UP045
    impersonated_by: Mapped[Optional[int]] = mapped_column(sa.Integer(), nullable=True)  # noqa: UP045
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("NOW()"))
