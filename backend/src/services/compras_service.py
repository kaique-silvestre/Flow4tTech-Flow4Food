import math
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.fornecedores import Fornecedor
from src.models.insumos import Insumo
from src.models.movimentos_estoque import TipoMovimento
from src.repositories import compras_repository, estoque_repository
from src.schemas.compras import (
    CompraCreateRequest,
    CompraPatchRequest,
    CompraResponse,
    ComprasPageResponse,
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


def _get_fornecedor_nome(db: Session, fornecedor_id: Optional[int]) -> Optional[str]:
    if fornecedor_id is None:
        return None
    f = db.execute(select(Fornecedor).where(Fornecedor.id == fornecedor_id)).scalar_one_or_none()
    return f.nome if f else None


def criar_compra(db: Session, data: CompraCreateRequest) -> CompraResponse:
    warning = None
    if data.numero_nota:
        existing = compras_repository.find_by_numero_nota(db, data.numero_nota)
        if existing:
            warning = f"Número de nota já registrado na compra #{str(existing.id).zfill(4)}"

    try:
        total = Decimal("0")
        itens_processados = []

        for item_req in data.itens:
            insumo = estoque_repository.get_insumo_for_update(db, item_req.item_id)
            if insumo is None:
                raise AppError(
                    ErrorCode.NOT_FOUND,
                    f"Insumo {item_req.item_id} não encontrado",
                    http_status=404,
                )

            custo_unitario = (item_req.custo_total / item_req.quantidade).quantize(Decimal("0.0001"))
            novo_custo_medio = _calcular_custo_medio(
                insumo.estoque_atual,
                insumo.custo_medio,
                item_req.quantidade,
                custo_unitario,
            )
            novo_estoque = insumo.estoque_atual + item_req.quantidade

            estoque_repository.update_estoque_e_custo(
                db, insumo.id, novo_estoque, novo_custo_medio
            )
            total += item_req.custo_total

            itens_processados.append((insumo, item_req, custo_unitario, novo_estoque))

        compra = compras_repository.create_compra(
            db=db,
            fornecedor_id=data.fornecedor_id,
            data_compra=data.data_compra,
            numero_nota=data.numero_nota,
            total=total,
        )

        itens_response = []
        for insumo, item_req, custo_unitario, novo_estoque in itens_processados:
            compras_repository.add_item_compra(
                db=db,
                compra_id=compra.id,
                insumo_id=insumo.id,
                quantidade=item_req.quantidade,
                custo_unitario=custo_unitario,
                custo_total=item_req.custo_total,
            )
            estoque_repository.registrar_movimento(
                db=db,
                insumo_id=insumo.id,
                tipo=TipoMovimento.ENTRADA,
                quantidade=item_req.quantidade,
                custo_unitario=custo_unitario,
                saldo_apos=novo_estoque,
                compra_id=compra.id,
            )
            itens_response.append(
                ItemCompraResponse(
                    item_id=insumo.id,
                    item_nome=insumo.nome,
                    quantidade=item_req.quantidade,
                    custo_unitario=custo_unitario,
                    custo_total=item_req.custo_total,
                )
            )

        db.commit()
    except Exception:
        db.rollback()
        raise

    return CompraResponse(
        id=compra.id,
        fornecedor_id=compra.fornecedor_id,
        fornecedor_nome=_get_fornecedor_nome(db, compra.fornecedor_id),
        data_compra=compra.data_compra,
        numero_nota=compra.numero_nota,
        total=compra.total,
        status=compra.status,
        itens=itens_response,
        created_at=compra.created_at,
        warning=warning,
    )


def get_compra(db: Session, compra_id: int) -> CompraResponse:
    compra = compras_repository.get_compra_by_id(db, compra_id)
    if compra is None:
        raise AppError(ErrorCode.NOT_FOUND, "Compra não encontrada", http_status=404)

    itens_db = compras_repository.get_itens_compra(db, compra_id)
    itens_response = []
    for ic in itens_db:
        insumo = db.execute(select(Insumo).where(Insumo.id == ic.insumo_id)).scalar_one_or_none()
        itens_response.append(
            ItemCompraResponse(
                item_id=ic.insumo_id,
                item_nome=insumo.nome if insumo else "",
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
        status=getattr(compra, "status", "ativa"),
        itens=itens_response,
        created_at=compra.created_at,
    )


def _build_compra_response(db: Session, compra: Any) -> CompraResponse:
    itens_db = compras_repository.get_itens_compra(db, compra.id)
    itens_response = []
    for ic in itens_db:
        insumo = db.execute(select(Insumo).where(Insumo.id == ic.insumo_id)).scalar_one_or_none()
        itens_response.append(
            ItemCompraResponse(
                item_id=ic.insumo_id,
                item_nome=insumo.nome if insumo else "",
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
        status=compra.status,
        itens=itens_response,
        created_at=compra.created_at,
    )


def cancelar_compra(db: Session, compra_id: int) -> CompraResponse:
    compra = compras_repository.get_compra_by_id(db, compra_id)
    if compra is None:
        raise AppError(ErrorCode.NOT_FOUND, "Compra não encontrada", http_status=404)
    if compra.status == "cancelada":
        raise AppError(ErrorCode.CONFLICT, "Compra já cancelada", http_status=409)

    try:
        itens = compras_repository.get_itens_compra(db, compra_id)
        for item in itens:
            insumo = estoque_repository.get_insumo_for_update(db, item.insumo_id)
            if insumo is None:
                continue
            novo_estoque = insumo.estoque_atual - item.quantidade
            estoque_repository.update_estoque_e_custo(db, insumo.id, novo_estoque, insumo.custo_medio)
            estoque_repository.registrar_movimento(
                db=db,
                insumo_id=insumo.id,
                tipo=TipoMovimento.ESTORNO_COMPRA,
                quantidade=-item.quantidade,
                custo_unitario=item.custo_unitario,
                saldo_apos=novo_estoque,
                compra_id=compra_id,
            )

        compra.status = "cancelada"
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(compra)
    return _build_compra_response(db, compra)


def patch_compra(db: Session, compra_id: int, data: CompraPatchRequest) -> CompraResponse:
    compra = compras_repository.get_compra_by_id(db, compra_id)
    if compra is None:
        raise AppError(ErrorCode.NOT_FOUND, "Compra não encontrada", http_status=404)
    if compra.status == "cancelada":
        raise AppError(ErrorCode.VALIDATION_ERROR, "Compra cancelada não pode ser editada", http_status=422)
    if data.fornecedor_id is not None:
        compra.fornecedor_id = data.fornecedor_id
    if data.data_compra is not None:
        compra.data_compra = data.data_compra
    if data.numero_nota is not None:
        compra.numero_nota = data.numero_nota
    db.commit()
    db.refresh(compra)
    return _build_compra_response(db, compra)


def list_compras(
    db: Session,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    fornecedor_id: Optional[int] = None,
    status: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 10,
) -> ComprasPageResponse:
    import datetime

    di = datetime.date.fromisoformat(data_inicio) if data_inicio else None
    df = datetime.date.fromisoformat(data_fim) if data_fim else None

    compras, total, total_periodo = compras_repository.list_compras(db, di, df, fornecedor_id, status, pagina, por_pagina)
    result = []
    for compra in compras:
        itens_db = compras_repository.get_itens_compra(db, compra.id)
        itens_response = []
        for ic in itens_db:
            insumo = db.execute(select(Insumo).where(Insumo.id == ic.insumo_id)).scalar_one_or_none()
            itens_response.append(
                ItemCompraResponse(
                    item_id=ic.insumo_id,
                    item_nome=insumo.nome if insumo else "",
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
                status=getattr(compra, "status", "ativa"),
                itens=itens_response,
                created_at=compra.created_at,
            )
        )
    return ComprasPageResponse(
        itens=result,
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=max(1, math.ceil(total / por_pagina)),
        total_periodo=total_periodo,
    )
