from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ConfigSeguranca(Base):
    __tablename__ = "config_seguranca"

    id: Mapped[int] = mapped_column(primary_key=True)
    senha_hash: Mapped[str] = mapped_column(nullable=False)
