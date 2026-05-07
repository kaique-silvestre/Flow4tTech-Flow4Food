import datetime
import json
from decimal import Decimal
from typing import Optional

from sqlalchemy import text
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from src.models.comandas import Comanda, StatusComanda
from src.models.eventos_comanda import EventoComanda, TipoEvento
from src.models.itens_comanda import ItemComanda
from src.schemas.comandas import ComandaCreateRequest


def create_comanda(db: Session, data: ComandaCreateRequest) -> Comanda:
    comanda = Comanda(
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
    q = db.query(Comanda).filter(Comanda.status == StatusComanda.ABERTA.value)
    if busca:
        q = q.filter(Comanda.identificacao.ilike(f"%{busca}%"))
    return q.order_by(Comanda.created_at.desc()).all()


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
        item_id=item_id,
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


def top_itens(db: Session, dias: int, limit: int) -> list[tuple[int, int]]:
    result = db.execute(
        text(
            "SELECT ic.item_id, COUNT(*) as cnt "
            "FROM itens_comanda ic "
            "JOIN comandas c ON c.id = ic.comanda_id "
            "WHERE ic.cancelado = 0 "
            "AND ic.created_at >= :since "
            "GROUP BY ic.item_id "
            "ORDER BY cnt DESC "
            "LIMIT :limit"
        ),
        {
            "since": datetime.datetime.utcnow() - datetime.timedelta(days=dias),
            "limit": limit,
        },
    )
    return [(row[0], row[1]) for row in result.fetchall()]
