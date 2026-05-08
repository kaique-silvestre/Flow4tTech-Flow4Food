from typing import Optional

from sqlalchemy.orm import Session

from src.models.estabelecimento import Estabelecimento


def get_estabelecimento(db: Session) -> Optional[Estabelecimento]:
    return db.get(Estabelecimento, 1)
