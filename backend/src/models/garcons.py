from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Garcom(Base):
    __tablename__ = "garcons"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(nullable=False)
    ativo: Mapped[bool] = mapped_column(nullable=False, default=True)
