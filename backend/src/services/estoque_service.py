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


def _get_categorias_nomes(db: Session, categoria_ids: set[int]) -> dict[int, str]:
    if not categoria_ids:
        return {}
    categorias = db.execute(select(Categoria).where(Categoria.id.in_(categoria_ids))).scalars().all()
    return {c.id: c.nome for c in categorias}


def _get_insumos_map(db: Session, insumo_ids: set[int]) -> dict[int, Insumo]:
    if not insumo_ids:
        return {}
    insumos = db.execute(select(Insumo).where(Insumo.id.in_(insumo_ids))).scalars().all()
    return {i.id: i for i in insumos}


def _get_insumo(db: Session, insumo_id: int) -> Optional[Insumo]:
    return db.execute(select(Insumo).where(Insumo.id == insumo_id)).scalar_one_or_none()


def _parse_optional_date(value: Optional[str], field: str) -> Optional[datetime.date]:
    if value is None:
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            f"{field} deve estar no formato AAAA-MM-DD",
            field=field,
            http_status=422,
        ) from None


def _build_movimento_response_from_insumo(
    mov: MovimentoEstoque, insumo: Optional[Insumo]
) -> MovimentoResponse:
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


def _build_movimento_response(db: Session, mov: MovimentoEstoque) -> MovimentoResponse:
    insumo = _get_insumo(db, mov.insumo_id)
    return _build_movimento_response_from_insumo(mov, insumo)


def _build_movimentos_response_list(
    db: Session, movimentos: list[MovimentoEstoque]
) -> list[MovimentoResponse]:
    insumo_ids = {m.insumo_id for m in movimentos}
    insumo_map = _get_insumos_map(db, insumo_ids)
    return [
        _build_movimento_response_from_insumo(m, insumo_map.get(m.insumo_id))
        for m in movimentos
    ]


def get_saldo_list(
    db: Session,
    categoria_id: Optional[int] = None,
    busca: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 500,
) -> SaldoPageResponse:
    import math
    insumos, total = estoque_repository.list_saldo(db, categoria_id, busca, pagina=pagina, por_pagina=por_pagina)
    categoria_ids = {i.categoria_id for i in insumos if i.categoria_id is not None}
    categoria_nomes = _get_categorias_nomes(db, categoria_ids)
    result = []
    for insumo in insumos:
        result.append(
            SaldoItemResponse(
                id=insumo.id,
                nome=insumo.nome,
                categoria_id=insumo.categoria_id,
                categoria_nome=categoria_nomes.get(insumo.categoria_id) if insumo.categoria_id is not None else None,
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


def baixa_sem_venda(
    db: Session,
    data: BaixaSemVendaRequest,
    user_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
) -> dict:
    insumo = estoque_repository.get_insumo_for_update(db, data.item_id, tenant_id)
    if insumo is None:
        raise AppError(ErrorCode.NOT_FOUND, "Insumo não encontrado", http_status=404)

    novo_saldo = insumo.estoque_atual - data.quantidade
    estoque_repository.update_estoque_e_custo(
        db, insumo.id, novo_saldo, insumo.custo_medio, tenant_id
    )
    mov = estoque_repository.registrar_movimento(
        db=db,
        insumo_id=insumo.id,
        tipo=TipoMovimento.SAIDA_PERDA,
        quantidade=data.quantidade,
        custo_unitario=insumo.custo_medio,
        saldo_apos=novo_saldo,
        motivo=data.motivo.value,
        observacao=data.observacao,
        user_id=user_id,
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
    di = _parse_optional_date(data_inicio, "data_inicio")
    df = _parse_optional_date(data_fim, "data_fim")

    movimentos, total = estoque_repository.list_movimentos(
        db, item_id, tipo, di, df, pagina, por_pagina
    )

    return MovimentoListResponse(
        itens=_build_movimentos_response_list(db, movimentos),
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
    di = _parse_optional_date(data_inicio, "data_inicio")
    df = _parse_optional_date(data_fim, "data_fim")
    if di:
        q = q.filter(ItemComanda.created_at >= datetime.datetime(di.year, di.month, di.day))
    if df:
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
