from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.pagamentos import Pagamento


def create_pagamento(
    db: Session,
    comanda_id: int,
    metodo_id: int,
    valor: Decimal,
    valor_nota: Optional[Decimal] = None,
    troco: Optional[Decimal] = None,
) -> Pagamento:
    pagamento = Pagamento(
        comanda_id=comanda_id,
        metodo_id=metodo_id,
        valor=valor,
        valor_nota=valor_nota,
        troco=troco,
    )
    db.add(pagamento)
    db.flush()
    return pagamento


def list_by_comanda(db: Session, comanda_id: int) -> list[Pagamento]:
    return list(
        db.execute(
            select(Pagamento).where(Pagamento.comanda_id == comanda_id).order_by(Pagamento.id)
        ).scalars().all()
    )
