from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.insumos import Insumo
from src.repositories import insumos_repository, produtos_repository
from src.schemas.produtos import (
    FichaTecnicaItemResponse,
    ProdutoCreateRequest,
    ProdutoResponse,
    ProdutoUpdateRequest,
)


def _build_response(db: Session, produto) -> ProdutoResponse:
    componentes = produtos_repository.get_ficha(db, produto.id)
    ficha_resp = None
    if componentes:
        ficha_resp = []
        for comp in componentes:
            insumo = db.execute(select(Insumo).where(Insumo.id == comp.insumo_id)).scalar_one_or_none()
            ficha_resp.append(FichaTecnicaItemResponse(
                insumo_id=comp.insumo_id,
                insumo_nome=insumo.nome if insumo else f"Insumo {comp.insumo_id}",
                quantidade=comp.quantidade,
                unidade_base=insumo.unidade_base if insumo else "un",
                custo_medio_insumo=insumo.custo_medio if insumo else None,
            ))
    return ProdutoResponse(
        id=produto.id,
        nome=produto.nome,
        categoria_id=produto.categoria_id,
        preco_venda=produto.preco_venda,
        ativo=produto.ativo,
        ficha_tecnica=ficha_resp,
    )


def list_produtos(
    db: Session,
    categoria_id: Optional[int] = None,
    busca: Optional[str] = None,
) -> list[ProdutoResponse]:
    items = produtos_repository.list_ativos(db, categoria_id, busca, ativo=None)
    return [_build_response(db, p) for p in items]


def get_produto(db: Session, produto_id: int) -> ProdutoResponse:
    obj = produtos_repository.get_by_id(db, produto_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Produto não encontrado", http_status=404)
    return _build_response(db, obj)


def create_produto(db: Session, data: ProdutoCreateRequest) -> ProdutoResponse:
    if data.ficha_tecnica:
        for comp in data.ficha_tecnica:
            insumo = insumos_repository.get_by_id(db, comp.insumo_id)
            if insumo is None:
                raise AppError(
                    ErrorCode.NOT_FOUND,
                    f"Insumo id={comp.insumo_id} não encontrado",
                    http_status=404,
                )

    obj = produtos_repository.create(db, data)
    if data.ficha_tecnica:
        produtos_repository.upsert_ficha(db, obj.id, data.ficha_tecnica)
    db.commit()
    db.refresh(obj)
    return _build_response(db, obj)


def update_produto(db: Session, produto_id: int, data: ProdutoUpdateRequest) -> ProdutoResponse:
    obj = produtos_repository.get_by_id(db, produto_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Produto não encontrado", http_status=404)

    if data.ficha_tecnica:
        for comp in data.ficha_tecnica:
            insumo = insumos_repository.get_by_id(db, comp.insumo_id)
            if insumo is None:
                raise AppError(
                    ErrorCode.NOT_FOUND,
                    f"Insumo id={comp.insumo_id} não encontrado",
                    http_status=404,
                )

    obj = produtos_repository.update(db, produto_id, data)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Produto não encontrado", http_status=404)
    produtos_repository.upsert_ficha(db, produto_id, data.ficha_tecnica or [])
    db.commit()
    db.refresh(obj)
    return _build_response(db, obj)


def delete_produto(db: Session, produto_id: int) -> None:
    obj = produtos_repository.get_by_id(db, produto_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Produto não encontrado", http_status=404)
    if produtos_repository.is_referenced_in_comanda(db, produto_id):
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Produto tem histórico em comandas e não pode ser excluído. Use 'Desativar'.",
            http_status=422,
        )
    db.delete(obj)
    db.commit()


def desativar_produto(db: Session, produto_id: int) -> ProdutoResponse:
    obj = produtos_repository.get_by_id(db, produto_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Produto não encontrado", http_status=404)
    obj.ativo = False
    db.commit()
    db.refresh(obj)
    return _build_response(db, obj)


def reativar_produto(db: Session, produto_id: int) -> ProdutoResponse:
    obj = produtos_repository.get_by_id(db, produto_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Produto não encontrado", http_status=404)
    obj.ativo = True
    db.commit()
    db.refresh(obj)
    return _build_response(db, obj)


def get_top_produtos(db: Session, dias: int, limit: int) -> list[ProdutoResponse]:
    import datetime

    from sqlalchemy import func

    from src.models.itens_comanda import ItemComanda

    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=dias)
    rows = db.execute(
        select(ItemComanda.produto_id, func.count(ItemComanda.id).label("cnt"))
        .where(
            ItemComanda.cancelado == False,  # noqa: E712
            ItemComanda.created_at >= cutoff,
        )
        .group_by(ItemComanda.produto_id)
        .order_by(func.count(ItemComanda.id).desc())
        .limit(limit)
    ).all()

    result = []
    for produto_id, _cnt in rows:
        obj = produtos_repository.get_by_id(db, produto_id)
        if obj and obj.ativo:
            result.append(_build_response(db, obj))
    return result
