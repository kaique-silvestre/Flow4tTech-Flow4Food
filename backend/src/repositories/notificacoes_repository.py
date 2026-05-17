from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.contas_pagar import Notificacao


def criar_notificacao(
    db: Session,
    tipo: str,
    mensagem: str,
    referencia_id: Optional[int] = None,
) -> Notificacao:
    n = Notificacao(tipo=tipo, mensagem=mensagem, referencia_id=referencia_id)
    db.add(n)
    return n


def notificacao_existe(db: Session, tipo: str, referencia_id: int) -> bool:
    return (
        db.execute(
            select(Notificacao).where(
                Notificacao.tipo == tipo,
                Notificacao.referencia_id == referencia_id,
                Notificacao.lida.is_(False),
            )
        ).scalar_one_or_none()
        is not None
    )


def list_pendentes(db: Session) -> list[Notificacao]:
    return list(
        db.execute(
            select(Notificacao).where(Notificacao.lida.is_(False)).order_by(Notificacao.created_at.desc())
        ).scalars().all()
    )


def marcar_lida(db: Session, notificacao_id: int) -> Optional[Notificacao]:
    n = db.execute(select(Notificacao).where(Notificacao.id == notificacao_id)).scalar_one_or_none()
    if n:
        n.lida = True
    return n
