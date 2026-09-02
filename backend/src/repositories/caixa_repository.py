import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from src.models.caixa import CaixaMovimento, CaixaSessao, StatusCaixa
from src.models.metodos_pagamento import MetodoPagamento
from src.models.pagamentos import Pagamento


def get_sessao_aberta(db: Session, for_update: bool = False) -> Optional[CaixaSessao]:
    stmt = (
        select(CaixaSessao)
        .where(CaixaSessao.status == StatusCaixa.ABERTA.value)
        .limit(1)
    )
    if for_update:
        # Locks the row for the transaction's duration so a concurrent
        # `fechar_sessao` on the same session serializes against this read
        # instead of racing it (no-op on dialects without row locking, e.g.
        # SQLite, which already serializes writes at the connection level).
        stmt = stmt.with_for_update()
    return db.execute(stmt).scalars().first()


def criar_sessao(db: Session, valor_abertura: Decimal, user_id: int) -> CaixaSessao:
    sessao = CaixaSessao(
        valor_abertura=valor_abertura,
        aberto_por_user_id=user_id,
        status=StatusCaixa.ABERTA.value,
    )
    db.add(sessao)
    db.flush()
    return sessao


def fechar_sessao(
    db: Session,
    sessao_id: int,
    valor_informado: Decimal,
    valor_esperado: Decimal,
    user_id: int,
    observacao: Optional[str] = None,
) -> Optional[CaixaSessao]:
    """Atomically closes a session iff it is still 'aberta'.

    Uses a conditional UPDATE (status = 'aberta' in the WHERE clause) as a
    compare-and-swap: if a concurrent close already flipped the status, this
    matches zero rows and returns None instead of silently overwriting the
    other close. Mirrors the optimistic-locking pattern used for `version`
    in comandas_repository.increment_version, but reuses the status
    transition itself as the guard so no schema migration is needed.
    """
    result: CursorResult = db.execute(  # type: ignore[assignment]
        update(CaixaSessao)
        .where(
            CaixaSessao.id == sessao_id,
            CaixaSessao.status == StatusCaixa.ABERTA.value,
        )
        .values(
            status=StatusCaixa.FECHADA.value,
            valor_informado=valor_informado,
            valor_esperado=valor_esperado,
            diferenca=valor_informado - valor_esperado,
            fechado_por_user_id=user_id,
            closed_at=datetime.datetime.utcnow(),
            observacao=observacao,
        )
    )
    db.expire_all()
    if result.rowcount == 0:
        return None
    return db.get(CaixaSessao, sessao_id)


def criar_movimento(
    db: Session,
    sessao_id: int,
    tipo: str,
    valor: Decimal,
    motivo: str,
    user_id: int,
) -> CaixaMovimento:
    mov = CaixaMovimento(
        sessao_id=sessao_id,
        tipo=tipo,
        valor=valor,
        motivo=motivo,
        user_id=user_id,
    )
    db.add(mov)
    db.flush()
    return mov


def list_movimentos(db: Session, sessao_id: int) -> list[CaixaMovimento]:
    return list(
        db.execute(
            select(CaixaMovimento)
            .where(CaixaMovimento.sessao_id == sessao_id)
            .order_by(CaixaMovimento.created_at)
        ).scalars().all()
    )


def sum_movimentos_tipo(db: Session, sessao_id: int, tipo: str) -> Decimal:
    result = db.execute(
        select(func.sum(CaixaMovimento.valor)).where(
            CaixaMovimento.sessao_id == sessao_id,
            CaixaMovimento.tipo == tipo,
        )
    ).scalar_one()
    return result or Decimal("0")


def sum_pagamentos_dinheiro(
    db: Session, opened_at: datetime.datetime, closed_at: Optional[datetime.datetime] = None
) -> Decimal:
    stmt = (
        select(func.sum(Pagamento.valor))
        .join(MetodoPagamento, Pagamento.metodo_id == MetodoPagamento.id)
        .where(
            MetodoPagamento.tipo == "dinheiro",
            Pagamento.created_at >= opened_at,
        )
    )
    if closed_at is not None:
        stmt = stmt.where(Pagamento.created_at <= closed_at)
    result = db.execute(stmt).scalar_one()
    return result or Decimal("0")
