from typing import Optional

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.garcons import Garcom
from src.schemas.garcons import GarcomCreateRequest, GarcomUpdateRequest


def list_all(
    db: Session,
    busca: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 500,
) -> tuple[list[Garcom], int]:
    stmt = select(Garcom).order_by(Garcom.nome)
    count_stmt = select(func.count()).select_from(Garcom)
    if busca:
        stmt = stmt.where(Garcom.nome.ilike(f"%{busca}%"))
        count_stmt = count_stmt.where(Garcom.nome.ilike(f"%{busca}%"))
    total = db.execute(count_stmt).scalar_one()
    offset = (pagina - 1) * por_pagina
    return list(db.execute(stmt.offset(offset).limit(por_pagina)).scalars().all()), total


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
