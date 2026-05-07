import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class FichaTecnica(Base):
    __tablename__ = "fichas_tecnicas"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_composto_id: Mapped[int] = mapped_column(
        sa.ForeignKey("itens.id"), nullable=False, unique=True
    )
