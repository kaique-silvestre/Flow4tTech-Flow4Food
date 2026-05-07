from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.itens import Item, TipoItem
from src.repositories import itens_repository
from src.schemas.itens import (
    ComponenteRequest,
    ComponenteResponse,
    ItemCreateRequest,
    ItemResponse,
    ItemUpdateRequest,
)


def _validate_domain(
    db: Session,
    tipo: str,
    vendavel: bool,
    preco_venda: Optional[Decimal],
    ficha: Optional[list[ComponenteRequest]],
) -> None:
    if not vendavel and preco_venda is not None:
        raise AppError(
            ErrorCode.PRECO_EM_NAO_VENDAVEL,
            "Item não-vendável não pode ter preço de venda",
            http_status=400,
        )
    if tipo == TipoItem.COMPOSTO:
        if not ficha:
            raise AppError(
                ErrorCode.FICHA_VAZIA,
                "Item composto exige ao menos um insumo na ficha técnica",
                http_status=400,
            )
        for comp in ficha:
            insumo = itens_repository.get_by_id(db, comp.insumo_id)
            if insumo is None:
                raise AppError(ErrorCode.NOT_FOUND, f"Insumo id={comp.insumo_id} não encontrado", http_status=404)
            if insumo.tipo == TipoItem.COMPOSTO:
                raise AppError(
                    ErrorCode.FICHA_ANINHADA_NAO_SUPORTADA,
                    "Ficha técnica não pode incluir outro item composto",
                    http_status=400,
                )


def _build_response(db: Session, item: Item) -> ItemResponse:
    custo_composto: Optional[Decimal] = None
    cmv_percentual: Optional[Decimal] = None
    componentes_resp: Optional[list[ComponenteResponse]] = None

    if item.tipo == TipoItem.COMPOSTO:
        ficha = itens_repository.get_ficha(db, item.id)
        if ficha:
            comps = itens_repository.get_componentes(db, ficha.id)
            componentes_resp = []
            custo_total = Decimal("0")
            custo_valido = True
            for comp in comps:
                insumo = itens_repository.get_by_id(db, comp.insumo_id)
                if insumo:
                    componentes_resp.append(ComponenteResponse(
                        insumo_id=comp.insumo_id,
                        insumo_nome=insumo.nome,
                        quantidade=comp.quantidade,
                        unidade_base=insumo.unidade_base,
                    ))
                    if insumo.custo_medio is not None:
                        custo_total += comp.quantidade * insumo.custo_medio
                    else:
                        custo_valido = False
            if custo_valido and componentes_resp:
                custo_composto = custo_total
                if item.preco_venda and item.preco_venda > 0:
                    cmv_percentual = (custo_total / item.preco_venda * 100).quantize(Decimal("0.01"))

    return ItemResponse(
        id=item.id,
        nome=item.nome,
        categoria_id=item.categoria_id,
        tipo=item.tipo,
        vendavel=item.vendavel,
        unidade_base=item.unidade_base,
        quantidade_caixa=item.quantidade_caixa,
        custo_medio=item.custo_medio,
        preco_venda=item.preco_venda,
        estoque_atual=item.estoque_atual,
        ativo=item.ativo,
        custo_composto=custo_composto,
        cmv_percentual=cmv_percentual,
        componentes=componentes_resp,
    )


def list_itens(
    db: Session,
    categoria_id: Optional[int] = None,
    tipo: Optional[str] = None,
    vendavel: Optional[bool] = None,
    busca: Optional[str] = None,
) -> list[ItemResponse]:
    items = itens_repository.list_with_filters(db, categoria_id, tipo, vendavel, busca)
    return [_build_response(db, item) for item in items]


def get_item(db: Session, item_id: int) -> ItemResponse:
    item = itens_repository.get_by_id(db, item_id)
    if item is None:
        raise AppError(ErrorCode.NOT_FOUND, "Item não encontrado", http_status=404)
    return _build_response(db, item)


def create_item(db: Session, data: ItemCreateRequest) -> ItemResponse:
    _validate_domain(db, data.tipo, data.vendavel, data.preco_venda, data.ficha_tecnica)
    item = itens_repository.create(db, data)
    if data.tipo == TipoItem.COMPOSTO and data.ficha_tecnica:
        itens_repository.upsert_ficha_tecnica(db, item.id, data.ficha_tecnica)
    return _build_response(db, item)


def update_item(db: Session, item_id: int, data: ItemUpdateRequest) -> ItemResponse:
    existing = itens_repository.get_by_id(db, item_id)
    if existing is None:
        raise AppError(ErrorCode.NOT_FOUND, "Item não encontrado", http_status=404)
    _validate_domain(db, data.tipo, data.vendavel, data.preco_venda, data.ficha_tecnica)
    item = itens_repository.update(db, item_id, data)
    if item is None:
        raise AppError(ErrorCode.NOT_FOUND, "Item não encontrado", http_status=404)
    if data.tipo == TipoItem.COMPOSTO and data.ficha_tecnica:
        itens_repository.upsert_ficha_tecnica(db, item_id, data.ficha_tecnica)
    return _build_response(db, item)


def delete_item(db: Session, item_id: int) -> None:
    item = itens_repository.get_by_id(db, item_id)
    if item is None:
        raise AppError(ErrorCode.NOT_FOUND, "Item não encontrado", http_status=404)
    if itens_repository.is_referenced_in_ficha(db, item_id):
        itens_repository.soft_delete(db, item_id)
    else:
        itens_repository.hard_delete(db, item_id)


def list_simples_ativos(db: Session) -> list[ItemResponse]:
    items = itens_repository.list_simples_ativos(db)
    return [_build_response(db, item) for item in items]
