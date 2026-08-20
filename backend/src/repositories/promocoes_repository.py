import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.models.promocoes import Promocao, PromocaoProduto
from src.schemas.promocoes import PromoçaoCreate, PromoçaoUpdate


def _to_list(val) -> Optional[list]:  # noqa: UP045
    if val is None:
        return None
    if isinstance(val, list):
        return val
    # JSON stored as string in some backends
    import json
    if isinstance(val, str):
        return json.loads(val)
    return list(val)


def _get_produto_ids(db: Session, promocao_id: int) -> list[int]:
    rows = db.query(PromocaoProduto).filter(PromocaoProduto.promocao_id == promocao_id).all()
    return [r.produto_id for r in rows]


def set_produtos(db: Session, promocao_id: int, produto_ids: list[int]) -> None:
    db.query(PromocaoProduto).filter(PromocaoProduto.promocao_id == promocao_id).delete()
    for pid in produto_ids:
        db.add(PromocaoProduto(promocao_id=promocao_id, produto_id=pid))


def list_all(db: Session, status: Optional[str] = "todas") -> list[Promocao]:  # noqa: UP045
    today = datetime.date.today()
    q = db.query(Promocao)
    if status == "ativas":
        q = q.filter(
            Promocao.data_inicio <= today,
            (Promocao.data_fim == None) | (Promocao.data_fim >= today),  # noqa: E711
        )
    elif status == "futuras":
        q = q.filter(Promocao.data_inicio > today)
    return q.order_by(Promocao.id).all()


def list_by_month(db: Session, year: int, month: int) -> list[Promocao]:
    start = datetime.date(year, month, 1)
    end = datetime.date(year + 1, 1, 1) if month == 12 else datetime.date(year, month + 1, 1)
    return (
        db.query(Promocao)
        .filter(
            Promocao.data_inicio < end,
            (Promocao.data_fim == None) | (Promocao.data_fim >= start),  # noqa: E711
        )
        .order_by(Promocao.id)
        .all()
    )


def get_by_id(db: Session, promocao_id: int) -> Optional[Promocao]:  # noqa: UP045
    return db.query(Promocao).filter(Promocao.id == promocao_id).first()


def create(db: Session, data: PromoçaoCreate, criado_por: Optional[int] = None) -> Promocao:  # noqa: UP045
    promo = Promocao(
        nome=data.nome,
        descricao=data.descricao,
        tipo_desconto=data.tipo_desconto,
        valor_desconto=data.valor_desconto,
        data_inicio=data.data_inicio,
        data_fim=data.data_fim,
        hora_inicio=data.hora_inicio,
        hora_fim=data.hora_fim,
        recorrencia=data.recorrencia,
        dias_semana=data.dias_semana,
        dias_mes=data.dias_mes,
        criado_por=criado_por,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        ativo=data.ativo,
    )
    db.add(promo)
    db.flush()
    set_produtos(db, promo.id, data.produto_ids)
    db.commit()
    db.refresh(promo)
    return promo


def update(db: Session, promo: Promocao, data: PromoçaoUpdate) -> Promocao:
    for field in ("nome", "descricao", "tipo_desconto", "valor_desconto",
                  "data_inicio", "data_fim", "hora_inicio", "hora_fim",
                  "recorrencia", "dias_semana", "dias_mes", "ativo"):
        val = getattr(data, field)
        if val is not None:
            setattr(promo, field, val)
    if data.produto_ids is not None:
        set_produtos(db, promo.id, data.produto_ids)
    db.commit()
    db.refresh(promo)
    return promo


def delete(db: Session, promo: Promocao) -> None:
    db.delete(promo)
    db.commit()
