import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.consumo_interno import ItemConsumoInterno
from src.models.ficha_tecnica import FichaTecnica
from src.models.insumos import Insumo
from src.models.movimentos_estoque import TipoMovimento
from src.models.produtos import Produto
from src.models.system_users import SystemUser
from src.repositories import estoque_repository
from src.schemas.consumo_interno import (
    ItemConsumoInternoResponse,
    LancarConsumoBatchRequest,
    LancarConsumoRequest,
    ResumoConsumidorResponse,
)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _get_produto(db: Session, produto_id: int) -> Produto:
    produto = db.execute(select(Produto).where(Produto.id == produto_id)).scalar_one_or_none()
    if produto is None:
        raise AppError(ErrorCode.NOT_FOUND, "Produto não encontrado", http_status=404)
    return produto


def _get_consumidor(db: Session, consumidor_id: int) -> SystemUser:
    user = db.execute(select(SystemUser).where(SystemUser.id == consumidor_id)).scalar_one_or_none()
    if user is None:
        raise AppError(ErrorCode.NOT_FOUND, "Consumidor não encontrado", http_status=404)
    return user


def _calcular_custo_unitario(db: Session, produto: Produto) -> Decimal:
    """Calculate unit cost from ficha técnica (sum of insumo costs) or fallback."""
    componentes = list(
        db.execute(select(FichaTecnica).where(FichaTecnica.produto_id == produto.id)).scalars().all()
    )
    if componentes:
        custo = Decimal("0")
        for comp in componentes:
            insumo = db.execute(select(Insumo).where(Insumo.id == comp.insumo_id)).scalar_one_or_none()
            if insumo and insumo.custo_medio:
                custo += comp.quantidade * insumo.custo_medio
        if custo > 0:
            return custo

    # Fallback: produto may map to a single insumo with same name, or use preco_venda
    # Try to find insumo with same name as produto
    insumo_direto = db.execute(
        select(Insumo).where(Insumo.nome == produto.nome)
    ).scalar_one_or_none()
    if insumo_direto and insumo_direto.custo_medio:
        return insumo_direto.custo_medio

    # Last fallback: preco_venda
    if produto.preco_venda:
        return Decimal(str(produto.preco_venda))

    return Decimal("0")


def _dar_baixa_estoque_consumo(db: Session, produto_id: int, quantidade: Decimal) -> None:
    """Debit stock immediately for each insumo in ficha técnica."""
    componentes = list(
        db.execute(select(FichaTecnica).where(FichaTecnica.produto_id == produto_id)).scalars().all()
    )
    if not componentes:
        return

    for comp in componentes:
        insumo = estoque_repository.get_insumo_for_update(db, comp.insumo_id)
        if insumo is None:
            continue
        qty = comp.quantidade * quantidade
        novo_saldo = insumo.estoque_atual - qty
        insumo.estoque_atual = novo_saldo
        estoque_repository.registrar_movimento(
            db,
            insumo_id=insumo.id,
            tipo=TipoMovimento.SAIDA_CONSUMO_INTERNO,
            quantidade=qty,
            custo_unitario=insumo.custo_medio,
            saldo_apos=novo_saldo,
        )
    db.flush()


def _devolver_estoque_consumo(db: Session, produto_id: int, quantidade: Decimal) -> None:
    """Reverse stock debit on estorno."""
    componentes = list(
        db.execute(select(FichaTecnica).where(FichaTecnica.produto_id == produto_id)).scalars().all()
    )
    if not componentes:
        return

    for comp in componentes:
        insumo = estoque_repository.get_insumo_for_update(db, comp.insumo_id)
        if insumo is None:
            continue
        qty = comp.quantidade * quantidade
        novo_saldo = insumo.estoque_atual + qty
        insumo.estoque_atual = novo_saldo
        estoque_repository.registrar_movimento(
            db,
            insumo_id=insumo.id,
            tipo=TipoMovimento.ENTRADA_ESTORNO,
            quantidade=qty,
            custo_unitario=insumo.custo_medio,
            saldo_apos=novo_saldo,
            observacao="Estorno consumo interno",
        )
    db.flush()


def _build_response(db: Session, item: ItemConsumoInterno) -> ItemConsumoInternoResponse:
    consumidor = db.execute(select(SystemUser).where(SystemUser.id == item.consumidor_id)).scalar_one_or_none()
    produto = db.execute(select(Produto).where(Produto.id == item.produto_id)).scalar_one_or_none()
    return ItemConsumoInternoResponse(
        id=item.id,
        consumidor_id=item.consumidor_id,
        consumidor_nome=consumidor.name if consumidor else f"Usuário {item.consumidor_id}",
        produto_id=item.produto_id,
        produto_nome=produto.nome if produto else f"Produto {item.produto_id}",
        quantidade=item.quantidade,
        custo_unitario=item.custo_unitario,
        subtotal=item.quantidade * item.custo_unitario,
        observacao=item.observacao,
        created_at=item.created_at,
    )


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def lancar_item(db: Session, data: LancarConsumoRequest) -> ItemConsumoInternoResponse:
    """Create consumo interno record, debit stock immediately."""
    produto = _get_produto(db, data.produto_id)
    _get_consumidor(db, data.consumidor_id)

    custo_unitario = _calcular_custo_unitario(db, produto)

    item = ItemConsumoInterno(
        consumidor_id=data.consumidor_id,
        produto_id=data.produto_id,
        quantidade=data.quantidade,
        custo_unitario=custo_unitario,
        observacao=data.observacao,
    )
    db.add(item)
    db.flush()

    _dar_baixa_estoque_consumo(db, data.produto_id, data.quantidade)

    db.commit()
    db.refresh(item)
    return _build_response(db, item)


def lancar_batch(db: Session, data: LancarConsumoBatchRequest) -> list[ItemConsumoInternoResponse]:
    _get_consumidor(db, data.consumidor_id)
    items = []
    for item_data in data.itens:
        produto = _get_produto(db, item_data.produto_id)
        custo_unitario = _calcular_custo_unitario(db, produto)
        item = ItemConsumoInterno(
            consumidor_id=data.consumidor_id,
            produto_id=item_data.produto_id,
            quantidade=item_data.quantidade,
            custo_unitario=custo_unitario,
            observacao=item_data.observacao,
        )
        db.add(item)
        db.flush()
        _dar_baixa_estoque_consumo(db, item_data.produto_id, item_data.quantidade)
        items.append(item)
    db.commit()
    for item in items:
        db.refresh(item)
    return [_build_response(db, item) for item in items]


def estornar_item(db: Session, item_id: int) -> dict:
    """Reverse a consumo interno entry: restore stock and delete record."""
    item = db.execute(
        select(ItemConsumoInterno).where(ItemConsumoInterno.id == item_id)
    ).scalar_one_or_none()
    if item is None:
        raise AppError(ErrorCode.NOT_FOUND, "Item de consumo interno não encontrado", http_status=404)

    _devolver_estoque_consumo(db, item.produto_id, item.quantidade)
    db.delete(item)
    db.commit()
    return {"ok": True}


def listar_items(
    db: Session,
    consumidor_id: Optional[int] = None,
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    data_inicio: Optional[datetime.date] = None,
    data_fim: Optional[datetime.date] = None,
) -> list[ItemConsumoInternoResponse]:
    """List consumo interno items with optional filters."""
    stmt = select(ItemConsumoInterno).order_by(ItemConsumoInterno.created_at.desc())

    if consumidor_id is not None:
        stmt = stmt.where(ItemConsumoInterno.consumidor_id == consumidor_id)

    if data_inicio and data_fim:
        stmt = stmt.where(
            ItemConsumoInterno.created_at >= datetime.datetime.combine(data_inicio, datetime.time.min),
            ItemConsumoInterno.created_at <= datetime.datetime.combine(data_fim, datetime.time.max),
        )
    else:
        if mes is not None:
            stmt = stmt.where(extract("month", ItemConsumoInterno.created_at) == mes)
        if ano is not None:
            stmt = stmt.where(extract("year", ItemConsumoInterno.created_at) == ano)

    items = list(db.execute(stmt).scalars().all())
    return [_build_response(db, i) for i in items]


def resumo_mensal(
    db: Session,
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    data_inicio: Optional[datetime.date] = None,
    data_fim: Optional[datetime.date] = None,
) -> list[ResumoConsumidorResponse]:
    """Aggregate consumo by consumidor for a given period."""
    stmt = select(
        ItemConsumoInterno.consumidor_id,
        func.count(ItemConsumoInterno.id).label("itens_no_mes"),
        func.sum(ItemConsumoInterno.quantidade * ItemConsumoInterno.custo_unitario).label("total"),
        func.max(ItemConsumoInterno.created_at).label("ultima_atividade"),
    )

    if data_inicio and data_fim:
        stmt = stmt.where(
            ItemConsumoInterno.created_at >= datetime.datetime.combine(data_inicio, datetime.time.min),
            ItemConsumoInterno.created_at <= datetime.datetime.combine(data_fim, datetime.time.max),
        )
    else:
        now = datetime.datetime.now()
        mes = mes or now.month
        ano = ano or now.year
        stmt = stmt.where(
            extract("month", ItemConsumoInterno.created_at) == mes,
            extract("year", ItemConsumoInterno.created_at) == ano,
        )

    stmt = stmt.group_by(ItemConsumoInterno.consumidor_id)

    rows = db.execute(stmt).all()
    result = []
    for row in rows:
        consumidor = db.execute(
            select(SystemUser).where(SystemUser.id == row.consumidor_id)
        ).scalar_one_or_none()
        result.append(
            ResumoConsumidorResponse(
                consumidor_id=row.consumidor_id,
                consumidor_nome=consumidor.name if consumidor else f"Usuário {row.consumidor_id}",
                itens_no_mes=row.itens_no_mes,
                total=row.total or Decimal("0"),
                ultima_atividade=row.ultima_atividade,
            )
        )
    return result
