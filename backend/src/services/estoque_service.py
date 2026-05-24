import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.categorias import Categoria
from src.models.comandas import Comanda
from src.models.insumos import Insumo
from src.models.itens_comanda import ItemComanda
from src.models.movimentos_estoque import MovimentoEstoque, TipoMovimento
from src.models.produtos import Produto
from src.repositories import estoque_repository
from src.schemas.estoque import (
    BaixaSemVendaRequest,
    InsumoCriticoResponse,
    MovimentoListResponse,
    MovimentoProdutoListResponse,
    MovimentoProdutoResponse,
    MovimentoResponse,
    SaldoItemResponse,
    SaldoPageResponse,
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
    pagina: int = 1,
    por_pagina: int = 500,
) -> SaldoPageResponse:
    import math
    insumos, total = estoque_repository.list_saldo(db, categoria_id, busca, pagina=pagina, por_pagina=por_pagina)
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
                nivel_critico=insumo.nivel_critico,
            )
        )
    return SaldoPageResponse(
        itens=result,
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=math.ceil(total / por_pagina) if total > 0 else 1,
    )


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


def get_historico_produtos(
    db: Session,
    produto_id: Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 50,
) -> MovimentoProdutoListResponse:
    q = (
        db.query(ItemComanda, Produto, Comanda)
        .join(Produto, Produto.id == ItemComanda.produto_id)
        .join(Comanda, Comanda.id == ItemComanda.comanda_id)
    )

    if produto_id:
        q = q.filter(ItemComanda.produto_id == produto_id)
    if data_inicio:
        di = datetime.date.fromisoformat(data_inicio)
        q = q.filter(ItemComanda.created_at >= datetime.datetime(di.year, di.month, di.day))
    if data_fim:
        df = datetime.date.fromisoformat(data_fim)
        q = q.filter(ItemComanda.created_at < datetime.datetime(df.year, df.month, df.day) + datetime.timedelta(days=1))

    total = q.count()
    rows = (
        q.order_by(ItemComanda.created_at.desc())
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
        .all()
    )

    itens = [
        MovimentoProdutoResponse(
            id=ic.id,
            produto_id=ic.produto_id,
            produto_nome=p.nome,
            comanda_id=ic.comanda_id,
            comanda_label=f"#{c.numero_dia or c.id} — {c.identificacao}",
            quantidade=ic.quantidade,
            preco_unitario=ic.preco_unitario,
            subtotal=Decimal("0") if ic.cortesia else ic.quantidade * ic.preco_unitario,
            cortesia=ic.cortesia,
            cancelado=ic.cancelado,
            pessoa_associada=ic.pessoa_associada,
            created_at=ic.created_at,
        )
        for ic, p, c in rows
    ]

    return MovimentoProdutoListResponse(
        itens=itens,
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
    )
