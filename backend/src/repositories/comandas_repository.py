import datetime
import json
from decimal import Decimal
from typing import Optional

from sqlalchemy import cast, func, select, text
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session
from sqlalchemy.types import Date

from src.models.comandas import Comanda, StatusComanda
from src.models.eventos_comanda import EventoComanda, TipoEvento
from src.models.itens_comanda import ItemComanda
from src.schemas.comandas import ComandaCreateRequest


def _next_numero_dia(db: Session) -> int:
    today = datetime.date.today()
    result = db.execute(
        select(func.max(Comanda.numero_dia)).where(
            cast(Comanda.created_at, Date) == today
        )
    ).scalar()
    return (result or 0) + 1


def create_comanda(db: Session, data: ComandaCreateRequest) -> Comanda:
    comanda = Comanda(
        numero_dia=_next_numero_dia(db),
        identificacao=data.identificacao,
        tipo_identificacao=data.tipo_identificacao,
        garcom_id=data.garcom_id,
        status=StatusComanda.ABERTA.value,
        version=1,
        pessoas=json.dumps(data.pessoas) if data.pessoas else json.dumps([]),
    )
    db.add(comanda)
    db.flush()
    return comanda


def list_abertas(db: Session, busca: Optional[str] = None) -> list[Comanda]:
    q = db.query(Comanda).filter(
        Comanda.status.in_([StatusComanda.ABERTA.value, StatusComanda.REABERTA.value])
    )
    if busca:
        q = q.filter(Comanda.identificacao.ilike(f"%{busca}%"))
    return q.order_by(Comanda.created_at.desc()).all()


def count_abertas(db: Session) -> int:
    return db.query(Comanda).filter(
        Comanda.status.in_([StatusComanda.ABERTA.value, StatusComanda.REABERTA.value])
    ).count()


def list_fechadas(
    db: Session,
    busca: Optional[str] = None,
    data_inicio: Optional[datetime.datetime] = None,
    data_fim: Optional[datetime.datetime] = None,
) -> list[Comanda]:
    q = db.query(Comanda).filter(Comanda.status == StatusComanda.FECHADA.value)
    if busca:
        q = q.filter(Comanda.identificacao.ilike(f"%{busca}%"))
    if data_inicio:
        q = q.filter(Comanda.data_fechamento >= data_inicio)
    if data_fim:
        q = q.filter(Comanda.data_fechamento <= data_fim)
    return q.order_by(Comanda.data_fechamento.desc()).all()


def get_by_id(db: Session, comanda_id: int) -> Optional[Comanda]:
    return db.query(Comanda).filter(Comanda.id == comanda_id).first()


def increment_version(db: Session, comanda_id: int, version_esperada: int) -> bool:
    result: CursorResult = db.execute(  # type: ignore[assignment]
        text(
            "UPDATE comandas SET version = version + 1, updated_at = :now "
            "WHERE id = :id AND version = :version"
        ),
        {"id": comanda_id, "version": version_esperada, "now": datetime.datetime.utcnow()},
    )
    db.expire_all()
    return result.rowcount > 0


def add_item(
    db: Session,
    comanda_id: int,
    item_id: int,
    quantidade: Decimal,
    preco_unitario: Decimal,
    pessoa_associada: Optional[str],
    observacao: Optional[str],
    cortesia: bool,
) -> ItemComanda:
    item_comanda = ItemComanda(
        comanda_id=comanda_id,
        produto_id=item_id,
        quantidade=quantidade,
        preco_unitario=preco_unitario,
        pessoa_associada=pessoa_associada,
        observacao=observacao,
        cortesia=cortesia,
        cancelado=False,
        estornado=False,
    )
    db.add(item_comanda)
    db.flush()
    return item_comanda


def get_item(db: Session, item_id: int) -> Optional[ItemComanda]:
    return db.query(ItemComanda).filter(ItemComanda.id == item_id).first()


def update_item(
    db: Session,
    item_id: int,
    quantidade: Optional[Decimal],
    pessoa_associada: Optional[str],
    observacao: Optional[str],
) -> Optional[ItemComanda]:
    item = db.query(ItemComanda).filter(ItemComanda.id == item_id).first()
    if item is None:
        return None
    if quantidade is not None:
        item.quantidade = quantidade
    if pessoa_associada is not None:
        item.pessoa_associada = pessoa_associada
    if observacao is not None:
        item.observacao = observacao
    db.flush()
    return item


def cancelar_item(
    db: Session,
    item_id: int,
    motivo: str,
    estornado: bool,
) -> Optional[ItemComanda]:
    item = db.query(ItemComanda).filter(ItemComanda.id == item_id).first()
    if item is None:
        return None
    item.cancelado = True
    item.motivo_cancelamento = motivo
    item.estornado = estornado
    db.flush()
    return item


def get_itens_ativos(db: Session, comanda_id: int) -> list[ItemComanda]:
    return (
        db.query(ItemComanda)
        .filter(ItemComanda.comanda_id == comanda_id)
        .order_by(ItemComanda.created_at.asc())
        .all()
    )


def add_evento(
    db: Session,
    comanda_id: int,
    tipo: TipoEvento,
    payload_dict: Optional[dict] = None,
    garcom_id: Optional[int] = None,
) -> EventoComanda:
    evento = EventoComanda(
        comanda_id=comanda_id,
        tipo=tipo.value,
        payload=json.dumps(payload_dict) if payload_dict else None,
        garcom_id=garcom_id,
    )
    db.add(evento)
    db.flush()
    return evento


def atualizar_desconto(
    db: Session,
    comanda_id: int,
    desconto_percentual: Optional[Decimal],
    desconto_valor: Optional[Decimal],
) -> None:
    comanda = db.query(Comanda).filter(Comanda.id == comanda_id).first()
    if comanda is not None:
        comanda.desconto_percentual = desconto_percentual
        comanda.desconto_valor = desconto_valor
    db.flush()


def fechar_comanda_repo(db: Session, comanda_id: int, total: Decimal) -> None:
    comanda = db.query(Comanda).filter(Comanda.id == comanda_id).first()
    if comanda is not None:
        comanda.status = StatusComanda.FECHADA.value
        comanda.total = total
        comanda.data_fechamento = datetime.datetime.utcnow()
    db.flush()


def atualizar_saldo_pendente(db: Session, comanda_id: int, saldo: Decimal) -> None:
    comanda = db.query(Comanda).filter(Comanda.id == comanda_id).first()
    if comanda is not None:
        comanda.saldo_pendente = saldo
    db.flush()


def get_itens_para_fechar(db: Session, comanda_id: int) -> list[ItemComanda]:
    return (
        db.query(ItemComanda)
        .filter(ItemComanda.comanda_id == comanda_id, ItemComanda.cancelado == False)  # noqa: E712
        .order_by(ItemComanda.created_at.asc())
        .all()
    )


def reabrir_comanda_repo(db: Session, comanda_id: int) -> None:
    comanda = db.query(Comanda).filter(Comanda.id == comanda_id).first()
    if comanda is not None:
        comanda.status = StatusComanda.REABERTA.value
        comanda.total = None
        comanda.data_fechamento = None
        comanda.saldo_pendente = None
    db.flush()


def cancelar_comanda_repo(db: Session, comanda_id: int) -> None:
    comanda = db.query(Comanda).filter(Comanda.id == comanda_id).first()
    if comanda is not None:
        comanda.status = StatusComanda.CANCELADA.value
    db.flush()


def top_itens(db: Session, dias: int, limit: int) -> list[tuple[int, int]]:
    result = db.execute(
        text(
            "SELECT ic.produto_id, COUNT(*) as cnt "
            "FROM itens_comanda ic "
            "JOIN comandas c ON c.id = ic.comanda_id "
            "WHERE ic.cancelado = false "
            "AND ic.created_at >= :since "
            "GROUP BY ic.produto_id "
            "ORDER BY cnt DESC "
            "LIMIT :limit"
        ),
        {
            "since": datetime.datetime.utcnow() - datetime.timedelta(days=dias),
            "limit": limit,
        },
    )
    return [(row[0], row[1]) for row in result.fetchall()]
