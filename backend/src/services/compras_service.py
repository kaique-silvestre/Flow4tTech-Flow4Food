from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.fornecedores import Fornecedor
from src.models.itens import Item
from src.models.movimentos_estoque import TipoMovimento
from src.repositories import compras_repository, estoque_repository
from src.schemas.compras import (
    CompraCreateRequest,
    CompraResponse,
    ItemCompraResponse,
)


def _calcular_custo_medio(
    estoque_atual: Decimal,
    custo_medio_atual: Optional[Decimal],
    quantidade_nova: Decimal,
    custo_unitario_novo: Decimal,
) -> Decimal:
    if estoque_atual <= 0 or custo_medio_atual is None:
        return custo_unitario_novo
    numerador = estoque_atual * custo_medio_atual + quantidade_nova * custo_unitario_novo
    denominador = estoque_atual + quantidade_nova
    return numerador / denominador


def _build_item_response(
    db: Session, item_compra_id: int, item_id: int, quantidade: Decimal,
    custo_unitario: Decimal, custo_total: Decimal
) -> ItemCompraResponse:
    item = db.execute(select(Item).where(Item.id == item_id)).scalar_one_or_none()
    nome = item.nome if item else ""
    return ItemCompraResponse(
        item_id=item_id,
        item_nome=nome,
        quantidade=quantidade,
        custo_unitario=custo_unitario,
        custo_total=custo_total,
    )


def _get_fornecedor_nome(db: Session, fornecedor_id: Optional[int]) -> Optional[str]:
    if fornecedor_id is None:
        return None
    f = db.execute(select(Fornecedor).where(Fornecedor.id == fornecedor_id)).scalar_one_or_none()
    return f.nome if f else None


def criar_compra(db: Session, data: CompraCreateRequest) -> CompraResponse:
    total = Decimal("0")
    itens_processados = []

    for item_req in data.itens:
        item = estoque_repository.get_item_for_update(db, item_req.item_id)
        if item is None:
            raise AppError(
                ErrorCode.NOT_FOUND,
                f"Item {item_req.item_id} não encontrado",
                http_status=404,
            )

        custo_unitario = item_req.custo_total / item_req.quantidade
        novo_custo_medio = _calcular_custo_medio(
            item.estoque_atual,
            item.custo_medio,
            item_req.quantidade,
            custo_unitario,
        )
        novo_estoque = item.estoque_atual + item_req.quantidade

        estoque_repository.update_estoque_e_custo(
            db, item.id, novo_estoque, novo_custo_medio
        )
        total += item_req.custo_total

        itens_processados.append((item, item_req, custo_unitario, novo_estoque))

    compra = compras_repository.create_compra(
        db=db,
        fornecedor_id=data.fornecedor_id,
        data_compra=data.data_compra,
        numero_nota=data.numero_nota,
        total=total,
    )

    itens_response = []
    for item, item_req, custo_unitario, novo_estoque in itens_processados:
        compras_repository.add_item_compra(
            db=db,
            compra_id=compra.id,
            item_id=item.id,
            quantidade=item_req.quantidade,
            custo_unitario=custo_unitario,
            custo_total=item_req.custo_total,
        )
        estoque_repository.registrar_movimento(
            db=db,
            item_id=item.id,
            tipo=TipoMovimento.ENTRADA,
            quantidade=item_req.quantidade,
            custo_unitario=custo_unitario,
            saldo_apos=novo_estoque,
            compra_id=compra.id,
        )
        itens_response.append(
            ItemCompraResponse(
                item_id=item.id,
                item_nome=item.nome,
                quantidade=item_req.quantidade,
                custo_unitario=custo_unitario,
                custo_total=item_req.custo_total,
            )
        )

    db.commit()

    return CompraResponse(
        id=compra.id,
        fornecedor_id=compra.fornecedor_id,
        fornecedor_nome=_get_fornecedor_nome(db, compra.fornecedor_id),
        data_compra=compra.data_compra,
        numero_nota=compra.numero_nota,
        total=compra.total,
        itens=itens_response,
        created_at=compra.created_at,
    )


def get_compra(db: Session, compra_id: int) -> CompraResponse:
    compra = compras_repository.get_compra_by_id(db, compra_id)
    if compra is None:
        raise AppError(ErrorCode.NOT_FOUND, "Compra não encontrada", http_status=404)

    itens_db = compras_repository.get_itens_compra(db, compra_id)
    itens_response = []
    for ic in itens_db:
        item = db.execute(select(Item).where(Item.id == ic.item_id)).scalar_one_or_none()
        itens_response.append(
            ItemCompraResponse(
                item_id=ic.item_id,
                item_nome=item.nome if item else "",
                quantidade=ic.quantidade,
                custo_unitario=ic.custo_unitario,
                custo_total=ic.custo_total,
            )
        )

    return CompraResponse(
        id=compra.id,
        fornecedor_id=compra.fornecedor_id,
        fornecedor_nome=_get_fornecedor_nome(db, compra.fornecedor_id),
        data_compra=compra.data_compra,
        numero_nota=compra.numero_nota,
        total=compra.total,
        itens=itens_response,
        created_at=compra.created_at,
    )


def list_compras(
    db: Session,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    fornecedor_id: Optional[int] = None,
) -> list[CompraResponse]:
    import datetime

    di = datetime.date.fromisoformat(data_inicio) if data_inicio else None
    df = datetime.date.fromisoformat(data_fim) if data_fim else None

    compras = compras_repository.list_compras(db, di, df, fornecedor_id)
    result = []
    for compra in compras:
        itens_db = compras_repository.get_itens_compra(db, compra.id)
        itens_response = []
        for ic in itens_db:
            item = db.execute(select(Item).where(Item.id == ic.item_id)).scalar_one_or_none()
            itens_response.append(
                ItemCompraResponse(
                    item_id=ic.item_id,
                    item_nome=item.nome if item else "",
                    quantidade=ic.quantidade,
                    custo_unitario=ic.custo_unitario,
                    custo_total=ic.custo_total,
                )
            )
        result.append(
            CompraResponse(
                id=compra.id,
                fornecedor_id=compra.fornecedor_id,
                fornecedor_nome=_get_fornecedor_nome(db, compra.fornecedor_id),
                data_compra=compra.data_compra,
                numero_nota=compra.numero_nota,
                total=compra.total,
                itens=itens_response,
                created_at=compra.created_at,
            )
        )
    return result
