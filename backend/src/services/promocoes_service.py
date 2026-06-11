import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.repositories import promocoes_repository
from src.schemas.promocoes import PromoçaoCreate, PromoçaoResponse, PromoçaoUpdate


def _build_response(promo, db: Session) -> PromoçaoResponse:
    produto_ids = promocoes_repository._get_produto_ids(db, promo.id)
    data = PromoçaoResponse.model_validate(promo)
    data.produto_ids = produto_ids
    return data


def list_promocoes(db: Session, status: Optional[str] = "todas") -> list[PromoçaoResponse]:  # noqa: UP045
    promos = promocoes_repository.list_all(db, status)
    return [_build_response(p, db) for p in promos]


def list_by_month(db: Session, mes: Optional[str]) -> list[PromoçaoResponse]:  # noqa: UP045
    if mes:
        try:
            dt = datetime.datetime.strptime(mes, "%Y-%m")
        except ValueError as exc:
            raise AppError(code=ErrorCode.VALIDATION_ERROR, message="Formato de mês inválido. Use YYYY-MM.", http_status=400) from exc
        year, month = dt.year, dt.month
    else:
        now = datetime.datetime.now()
        year, month = now.year, now.month
    promos = promocoes_repository.list_by_month(db, year, month)
    return [_build_response(p, db) for p in promos]


def criar_promocao(db: Session, data: PromoçaoCreate, criado_por: Optional[int] = None) -> PromoçaoResponse:  # noqa: UP045
    promo = promocoes_repository.create(db, data, criado_por)
    return _build_response(promo, db)


def update_promocao(db: Session, promocao_id: int, data: PromoçaoUpdate) -> PromoçaoResponse:
    promo = promocoes_repository.get_by_id(db, promocao_id)
    if promo is None:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Promoção não encontrada", http_status=404)
    promo = promocoes_repository.update(db, promo, data)
    return _build_response(promo, db)


def delete_promocao(db: Session, promocao_id: int) -> None:
    promo = promocoes_repository.get_by_id(db, promocao_id)
    if promo is None:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Promoção não encontrada", http_status=404)
    promocoes_repository.delete(db, promo)
