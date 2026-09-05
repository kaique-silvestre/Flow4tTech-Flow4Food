import datetime
from decimal import Decimal
from typing import Callable, Optional, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.ficha_tecnica import FichaTecnica
from src.models.insumos import Insumo
from src.models.movimentos_estoque import MovimentoEstoque, TipoMovimento

T = TypeVar("T")


def get_insumo_for_update(
    db: Session, insumo_id: int, tenant_id: Optional[int] = None
) -> Optional[Insumo]:
    stmt = select(Insumo).where(Insumo.id == insumo_id)
    if tenant_id is not None:
        stmt = stmt.where(Insumo.tenant_id == tenant_id)
    return db.execute(stmt.with_for_update()).scalar_one_or_none()


def ajustar_estoque_ficha_tecnica(
    db: Session,
    produto_id: int,
    quantidade: Decimal,
    ajustar_insumo: Callable[[Insumo, Decimal], Optional[T]],
    *,
    flush_each: bool = True,
) -> list[T]:
    """Itera os componentes da ficha técnica de um produto, travando (row
    lock via `get_insumo_for_update`) cada insumo referenciado, e aplica
    `ajustar_insumo` a cada um, na ordem dos componentes.

    `ajustar_insumo(insumo, quantidade_componente)` recebe o insumo já
    travado e a quantidade já multiplicada pela quantidade do produto
    (`comp.quantidade * quantidade`). Deve mutar o insumo e/ou registrar
    o movimento de estoque necessário; pode devolver um valor (ex.: nome
    do insumo) a ser coletado no resultado, ou `None` para não coletar
    nada nessa iteração.

    Componentes cujo insumo não é encontrado são ignorados (o mesmo
    comportamento que cada call site tinha antes da extração). Quando
    `flush_each` é True (padrão), o helper dá `db.flush()` após cada
    ajuste; quando False, cabe ao chamador (ou ao próprio
    `ajustar_insumo`) decidir quando dar flush — usado pelos call sites
    que já flushavam dentro de sua própria lógica de ajuste.
    """
    componentes = db.execute(
        select(FichaTecnica)
        .where(FichaTecnica.produto_id == produto_id)
        .order_by(FichaTecnica.insumo_id)
    ).scalars().all()
    resultados: list[T] = []
    for comp in componentes:
        insumo = get_insumo_for_update(db, comp.insumo_id)
        if insumo is None:
            continue
        resultado = ajustar_insumo(insumo, comp.quantidade * quantidade)
        if flush_each:
            db.flush()
        if resultado is not None:
            resultados.append(resultado)
    return resultados


def update_estoque_e_custo(
    db: Session,
    insumo_id: int,
    novo_estoque: Decimal,
    novo_custo_medio: Optional[Decimal],
    tenant_id: Optional[int] = None,
) -> None:
    stmt = select(Insumo).where(Insumo.id == insumo_id)
    if tenant_id is not None:
        stmt = stmt.where(Insumo.tenant_id == tenant_id)
    insumo = db.execute(stmt).scalar_one_or_none()
    if insumo is not None:
        insumo.estoque_atual = novo_estoque
        insumo.custo_medio = novo_custo_medio


def registrar_movimento(
    db: Session,
    insumo_id: int,
    tipo: TipoMovimento,
    quantidade: Decimal,
    custo_unitario: Optional[Decimal],
    saldo_apos: Decimal,
    motivo: Optional[str] = None,
    observacao: Optional[str] = None,
    compra_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> MovimentoEstoque:
    mov = MovimentoEstoque(
        insumo_id=insumo_id,
        tipo=tipo.value,
        quantidade=quantidade,
        custo_unitario=custo_unitario,
        saldo_apos=saldo_apos,
        motivo=motivo,
        observacao=observacao,
        compra_id=compra_id,
        user_id=user_id,
    )
    db.add(mov)
    db.flush()
    return mov


def list_saldo(
    db: Session,
    categoria_id: Optional[int] = None,
    busca: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 500,
) -> tuple[list[Insumo], int]:
    stmt = select(Insumo).where(Insumo.ativo == True).order_by(Insumo.nome)  # noqa: E712
    count_stmt = select(func.count()).select_from(Insumo).where(Insumo.ativo == True)  # noqa: E712
    if categoria_id is not None:
        stmt = stmt.where(Insumo.categoria_id == categoria_id)
        count_stmt = count_stmt.where(Insumo.categoria_id == categoria_id)
    if busca:
        stmt = stmt.where(Insumo.nome.ilike(f"%{busca}%"))
        count_stmt = count_stmt.where(Insumo.nome.ilike(f"%{busca}%"))
    total = db.execute(count_stmt).scalar_one()
    offset = (pagina - 1) * por_pagina
    return list(db.execute(stmt.offset(offset).limit(por_pagina)).scalars().all()), total


def list_movimentos(
    db: Session,
    insumo_id: Optional[int] = None,
    tipo: Optional[str] = None,
    data_inicio: Optional[datetime.date] = None,
    data_fim: Optional[datetime.date] = None,
    pagina: int = 1,
    por_pagina: int = 50,
) -> tuple[list[MovimentoEstoque], int]:
    stmt = select(MovimentoEstoque).order_by(MovimentoEstoque.created_at.desc(), MovimentoEstoque.id.desc())
    count_stmt = select(func.count()).select_from(MovimentoEstoque)

    if insumo_id is not None:
        stmt = stmt.where(MovimentoEstoque.insumo_id == insumo_id)
        count_stmt = count_stmt.where(MovimentoEstoque.insumo_id == insumo_id)
    if tipo is not None:
        stmt = stmt.where(MovimentoEstoque.tipo == tipo)
        count_stmt = count_stmt.where(MovimentoEstoque.tipo == tipo)
    if data_inicio is not None:
        stmt = stmt.where(func.date(MovimentoEstoque.created_at) >= data_inicio)
        count_stmt = count_stmt.where(func.date(MovimentoEstoque.created_at) >= data_inicio)
    if data_fim is not None:
        stmt = stmt.where(func.date(MovimentoEstoque.created_at) <= data_fim)
        count_stmt = count_stmt.where(func.date(MovimentoEstoque.created_at) <= data_fim)

    total = db.execute(count_stmt).scalar_one()
    offset = (pagina - 1) * por_pagina
    resultados = list(db.execute(stmt.offset(offset).limit(por_pagina)).scalars().all())
    return resultados, total
