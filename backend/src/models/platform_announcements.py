from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class PlatformAnnouncement(Base):
    __tablename__ = "platform_announcements"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    body: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(  # noqa: UP045
        sa.DateTime(timezone=True), nullable=True
    )
    target: Mapped[str] = mapped_column(sa.String(20), nullable=False, server_default="all")
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    created_by: Mapped[Optional[int]] = mapped_column(sa.BigInteger(), nullable=True)  # noqa: UP045
    created_at: Mapped[Optional[datetime]] = mapped_column(  # noqa: UP045
        sa.DateTime(timezone=True), server_default=sa.text("NOW()")
    )


class AnnouncementTarget(Base):
    __tablename__ = "announcement_targets"

    id: Mapped[int] = mapped_column(primary_key=True)
    announcement_id: Mapped[int] = mapped_column(
        sa.BigInteger(),
        sa.ForeignKey("platform_announcements.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False)


class AnnouncementRead(Base):
    __tablename__ = "announcement_reads"

    id: Mapped[int] = mapped_column(primary_key=True)
    announcement_id: Mapped[int] = mapped_column(
        sa.BigInteger(),
        sa.ForeignKey("platform_announcements.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False)
    tenant_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(  # noqa: UP045
        sa.DateTime(timezone=True), server_default=sa.text("NOW()")
    )
