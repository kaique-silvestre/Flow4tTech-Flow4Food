from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.componentes_ficha import ComponenteFicha
from src.models.fichas_tecnicas import FichaTecnica
from src.models.itens import Item, TipoItem
from src.schemas.itens import ComponenteRequest, ItemCreateRequest, ItemUpdateRequest


def list_with_filters(
    db: Session,
    categoria_id: Optional[int] = None,
    tipo: Optional[str] = None,
    vendavel: Optional[bool] = None,
    busca: Optional[str] = None,
) -> list[Item]:
    stmt = select(Item).where(Item.ativo == True)  # noqa: E712
    if categoria_id is not None:
        stmt = stmt.where(Item.categoria_id == categoria_id)
    if tipo is not None:
        stmt = stmt.where(Item.tipo == tipo)
    if vendavel is not None:
        stmt = stmt.where(Item.vendavel == vendavel)
    if busca:
        stmt = stmt.where(Item.nome.ilike(f"%{busca}%"))
    stmt = stmt.order_by(Item.nome)
    return list(db.execute(stmt).scalars().all())


def get_by_id(db: Session, item_id: int) -> Optional[Item]:
    return db.execute(select(Item).where(Item.id == item_id)).scalar_one_or_none()


def create(db: Session, data: ItemCreateRequest) -> Item:
    obj = Item(
        nome=data.nome,
        categoria_id=data.categoria_id,
        tipo=data.tipo,
        vendavel=data.vendavel,
        unidade_base=data.unidade_base,
        quantidade_caixa=data.quantidade_caixa,
        preco_venda=data.preco_venda,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, item_id: int, data: ItemUpdateRequest) -> Optional[Item]:
    obj = get_by_id(db, item_id)
    if obj is None:
        return None
    obj.nome = data.nome
    obj.categoria_id = data.categoria_id
    obj.tipo = data.tipo
    obj.vendavel = data.vendavel
    obj.unidade_base = data.unidade_base
    obj.quantidade_caixa = data.quantidade_caixa
    obj.preco_venda = data.preco_venda
    db.commit()
    db.refresh(obj)
    return obj


def soft_delete(db: Session, item_id: int) -> bool:
    obj = get_by_id(db, item_id)
    if obj is None:
        return False
    obj.ativo = False
    db.commit()
    return True


def hard_delete(db: Session, item_id: int) -> bool:
    obj = get_by_id(db, item_id)
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True


def is_referenced_in_ficha(db: Session, item_id: int) -> bool:
    result = db.execute(
        select(ComponenteFicha).where(ComponenteFicha.insumo_id == item_id).limit(1)
    ).scalar_one_or_none()
    return result is not None


def get_ficha(db: Session, item_id: int) -> Optional[FichaTecnica]:
    return db.execute(
        select(FichaTecnica).where(FichaTecnica.item_composto_id == item_id)
    ).scalar_one_or_none()


def get_componentes(db: Session, ficha_id: int) -> list[ComponenteFicha]:
    return list(
        db.execute(
            select(ComponenteFicha).where(ComponenteFicha.ficha_tecnica_id == ficha_id)
        ).scalars().all()
    )


def upsert_ficha_tecnica(
    db: Session, item_id: int, componentes: list[ComponenteRequest]
) -> FichaTecnica:
    ficha = get_ficha(db, item_id)
    if ficha is None:
        ficha = FichaTecnica(item_composto_id=item_id)
        db.add(ficha)
        db.flush()
    else:
        db.execute(
            select(ComponenteFicha).where(ComponenteFicha.ficha_tecnica_id == ficha.id)
        )
        existing = db.execute(
            select(ComponenteFicha).where(ComponenteFicha.ficha_tecnica_id == ficha.id)
        ).scalars().all()
        for c in existing:
            db.delete(c)
        db.flush()

    for comp in componentes:
        db.add(ComponenteFicha(
            ficha_tecnica_id=ficha.id,
            insumo_id=comp.insumo_id,
            quantidade=comp.quantidade,
        ))

    db.commit()
    db.refresh(ficha)
    return ficha


def calcular_custo_composto(db: Session, item_id: int) -> Optional[Decimal]:
    ficha = get_ficha(db, item_id)
    if ficha is None:
        return None
    componentes = get_componentes(db, ficha.id)
    if not componentes:
        return None
    total = Decimal("0")
    for comp in componentes:
        insumo = get_by_id(db, comp.insumo_id)
        if insumo is None or insumo.custo_medio is None:
            return None
        total += comp.quantidade * insumo.custo_medio
    return total


def list_simples_ativos(db: Session) -> list[Item]:
    return list(
        db.execute(
            select(Item)
            .where(Item.tipo == TipoItem.SIMPLES.value, Item.ativo == True)  # noqa: E712
            .order_by(Item.nome)
        ).scalars().all()
    )
