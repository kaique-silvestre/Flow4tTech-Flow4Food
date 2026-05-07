from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.garcons import Garcom
from src.schemas.garcons import GarcomCreateRequest, GarcomUpdateRequest


def list_all(db: Session) -> list[Garcom]:
    return list(db.execute(select(Garcom).order_by(Garcom.nome)).scalars().all())


def get_by_id(db: Session, garcom_id: int) -> Optional[Garcom]:
    return db.execute(select(Garcom).where(Garcom.id == garcom_id)).scalar_one_or_none()


def create(db: Session, data: GarcomCreateRequest) -> Garcom:
    obj = Garcom(nome=data.nome, ativo=True)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, garcom_id: int, data: GarcomUpdateRequest) -> Optional[Garcom]:
    obj = get_by_id(db, garcom_id)
    if obj is None:
        return None
    obj.nome = data.nome
    obj.ativo = data.ativo
    db.commit()
    db.refresh(obj)
    return obj
