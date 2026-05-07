import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.categorias import Categoria
from src.models.itens import Item, TipoItem
from src.models.movimentos_estoque import MovimentoEstoque, TipoMovimento
from src.repositories import estoque_repository
from src.schemas.estoque import (
    BaixaSemVendaRequest,
    MovimentoListResponse,
    MovimentoResponse,
    SaldoItemResponse,
)


def _get_categoria_nome(db: Session, categoria_id: Optional[int]) -> Optional[str]:
    if categoria_id is None:
        return None
    cat = db.execute(select(Categoria).where(Categoria.id == categoria_id)).scalar_one_or_none()
    return cat.nome if cat else None


def _get_item_nome(db: Session, item_id: int) -> str:
    item = db.execute(select(Item).where(Item.id == item_id)).scalar_one_or_none()
    return item.nome if item else ""


def _build_movimento_response(db: Session, mov: MovimentoEstoque) -> MovimentoResponse:
    return MovimentoResponse(
        id=mov.id,
        item_id=mov.item_id,
        item_nome=_get_item_nome(db, mov.item_id),
        tipo=mov.tipo,
        quantidade=mov.quantidade,
        custo_unitario=mov.custo_unitario,
        saldo_apos=mov.saldo_apos,
        motivo=mov.motivo,
        observacao=mov.observacao,
        compra_id=mov.compra_id,
        created_at=mov.created_at,
    )


def get_saldo_list(
    db: Session,
    categoria_id: Optional[int] = None,
    busca: Optional[str] = None,
) -> list[SaldoItemResponse]:
    itens = estoque_repository.list_saldo(db, categoria_id, busca)
    result = []
    for item in itens:
        result.append(
            SaldoItemResponse(
                id=item.id,
                nome=item.nome,
                categoria_id=item.categoria_id,
                categoria_nome=_get_categoria_nome(db, item.categoria_id),
                unidade_base=item.unidade_base,
                estoque_atual=item.estoque_atual,
                custo_medio=item.custo_medio,
            )
        )
    return result


def baixa_sem_venda(db: Session, data: BaixaSemVendaRequest) -> dict:
    item = estoque_repository.get_item_for_update(db, data.item_id)
    if item is None:
        raise AppError(ErrorCode.NOT_FOUND, "Item não encontrado", http_status=404)
    if item.tipo == TipoItem.COMPOSTO.value:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Item composto não possui estoque próprio",
            http_status=400,
        )

    novo_saldo = item.estoque_atual - data.quantidade
    estoque_repository.update_estoque_e_custo(db, item.id, novo_saldo, item.custo_medio)
    mov = estoque_repository.registrar_movimento(
        db=db,
        item_id=item.id,
        tipo=TipoMovimento.SAIDA_PERDA,
        quantidade=data.quantidade,
        custo_unitario=item.custo_medio,
        saldo_apos=novo_saldo,
        motivo=data.motivo.value,
        observacao=data.observacao,
    )
    db.commit()

    return {
        "movimento": _build_movimento_response(db, mov),
        "saldo_negativo": novo_saldo < Decimal("0"),
    }


def get_historico(
    db: Session,
    item_id: Optional[int] = None,
    tipo: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 50,
) -> MovimentoListResponse:
    di = datetime.date.fromisoformat(data_inicio) if data_inicio else None
    df = datetime.date.fromisoformat(data_fim) if data_fim else None

    movimentos, total = estoque_repository.list_movimentos(
        db, item_id, tipo, di, df, pagina, por_pagina
    )

    return MovimentoListResponse(
        itens=[_build_movimento_response(db, m) for m in movimentos],
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
    )
