import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.categorias import Categoria
from src.models.insumos import Insumo
from src.models.movimentos_estoque import MovimentoEstoque, TipoMovimento
from src.repositories import estoque_repository
from src.schemas.estoque import (
    BaixaSemVendaRequest,
    InsumoCriticoResponse,
    MovimentoListResponse,
    MovimentoResponse,
    SaldoItemResponse,
)


def _get_categoria_nome(db: Session, categoria_id: Optional[int]) -> Optional[str]:
    if categoria_id is None:
        return None
    cat = db.execute(select(Categoria).where(Categoria.id == categoria_id)).scalar_one_or_none()
    return cat.nome if cat else None


def _get_insumo(db: Session, insumo_id: int) -> Optional[Insumo]:
    return db.execute(select(Insumo).where(Insumo.id == insumo_id)).scalar_one_or_none()


def _build_movimento_response(db: Session, mov: MovimentoEstoque) -> MovimentoResponse:
    insumo = _get_insumo(db, mov.insumo_id)
    return MovimentoResponse(
        id=mov.id,
        item_id=mov.insumo_id,
        item_nome=insumo.nome if insumo else "",
        unidade_base=insumo.unidade_base if insumo else "un",
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
    insumos = estoque_repository.list_saldo(db, categoria_id, busca)
    result = []
    for insumo in insumos:
        result.append(
            SaldoItemResponse(
                id=insumo.id,
                nome=insumo.nome,
                categoria_id=insumo.categoria_id,
                categoria_nome=_get_categoria_nome(db, insumo.categoria_id),
                unidade_base=insumo.unidade_base,
                estoque_atual=insumo.estoque_atual,
                estoque_reservado=insumo.estoque_reservado,
                estoque_disponivel=insumo.estoque_atual - insumo.estoque_reservado,
                custo_medio=insumo.custo_medio,
            )
        )
    return result


def get_insumos_criticos(db: Session) -> list[InsumoCriticoResponse]:
    stmt = select(Insumo).where(Insumo.nivel_critico.isnot(None), Insumo.ativo == True)  # noqa: E712
    insumos = list(db.execute(stmt).scalars().all())
    result = []
    for i in insumos:
        disponivel = i.estoque_atual - i.estoque_reservado
        if i.nivel_critico is not None and disponivel < i.nivel_critico:
            result.append(InsumoCriticoResponse(
                id=i.id,
                nome=i.nome,
                unidade_base=i.unidade_base,
                estoque_disponivel=disponivel,
                nivel_critico=i.nivel_critico,
            ))
    return result


def baixa_sem_venda(db: Session, data: BaixaSemVendaRequest) -> dict:
    insumo = estoque_repository.get_insumo_for_update(db, data.item_id)
    if insumo is None:
        raise AppError(ErrorCode.NOT_FOUND, "Insumo não encontrado", http_status=404)

    novo_saldo = insumo.estoque_atual - data.quantidade
    estoque_repository.update_estoque_e_custo(db, insumo.id, novo_saldo, insumo.custo_medio)
    mov = estoque_repository.registrar_movimento(
        db=db,
        insumo_id=insumo.id,
        tipo=TipoMovimento.SAIDA_PERDA,
        quantidade=data.quantidade,
        custo_unitario=insumo.custo_medio,
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
