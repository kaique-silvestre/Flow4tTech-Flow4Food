from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.estabelecimento import Estabelecimento


def get_estabelecimento(db: Session) -> Optional[Estabelecimento]:
    return db.execute(select(Estabelecimento)).scalars().first()


def upsert_estabelecimento(
    db: Session,
    nome: Optional[str] = None,
    cnpj: Optional[str] = None,
    endereco: Optional[str] = None,
    telefone: Optional[str] = None,
) -> Estabelecimento:
    est = db.execute(select(Estabelecimento)).scalars().first()
    if est is None:
        est = Estabelecimento(nome=nome or "Estabelecimento")
        db.add(est)
    if nome is not None:
        est.nome = nome
    if cnpj is not None:
        est.cnpj = cnpj
    if endereco is not None:
        est.endereco = endereco
    if telefone is not None:
        est.telefone = telefone
    db.commit()
    db.refresh(est)
    return est
