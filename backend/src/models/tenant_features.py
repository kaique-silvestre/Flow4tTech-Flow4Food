from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class TenantFeature(Base):
    __tablename__ = "tenant_features"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    feature: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    enabled: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("NOW()"))
