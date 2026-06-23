import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Garcom(Base):
    __tablename__ = "garcons"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False, server_default=sa.text("(NULLIF(current_setting('app.tenant_id', true), ''))::bigint"))
    nome: Mapped[str] = mapped_column(nullable=False)
    ativo: Mapped[bool] = mapped_column(nullable=False, default=True)
