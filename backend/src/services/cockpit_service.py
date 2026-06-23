import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from src.models.compras import Compra, ItemCompra
from src.models.contas_pagar import ContaPagar
from src.models.eventos import TenantEvento
from src.models.fornecedores import Fornecedor
from src.models.insumos import Insumo
from src.models.promocoes import Promocao
from src.schemas.cockpit import CockpitItem


def _mes_range(mes: Optional[str]) -> tuple[datetime.date, datetime.date]:
    if not mes:
        today = datetime.date.today()
        mes = f"{today.year}-{today.month:02d}"
    year, month = (int(x) for x in mes.split("-"))
    start = datetime.date(year, month, 1)
    end = datetime.date(year + 1, 1, 1) if month == 12 else datetime.date(year, month + 1, 1)
    end_inclusive = end - datetime.timedelta(days=1)
    return start, end_inclusive


def list_consolidado(db: Session, mes: Optional[str], permissions: list[str]) -> list[CockpitItem]:
    start, end = _mes_range(mes)
    items: list[CockpitItem] = []

    # Layer 1: eventos (always, if calendario in permissions)
    if "calendario" in permissions:
        rows = db.execute(
            select(TenantEvento.id, TenantEvento.data_evento, TenantEvento.titulo, TenantEvento.hora_inicio, TenantEvento.hora_fim).where(
                and_(TenantEvento.data_evento >= start, TenantEvento.data_evento <= end)
            )
        ).all()
        for row in rows:
            items.append(CockpitItem(
                tipo="evento",
                referencia_id=row.id,
                data_referencia=row.data_evento,
                descricao=row.titulo,
                hora_inicio=row.hora_inicio,
                hora_fim=row.hora_fim,
            ))

    # Layer 2: promocoes (always, if calendario in permissions)
    if "calendario" in permissions:
        rows = db.execute(
            select(Promocao.id, Promocao.data_inicio, Promocao.nome, Promocao.hora_inicio).where(
                and_(
                    Promocao.data_inicio <= end,
                    or_(Promocao.data_fim.is_(None), Promocao.data_fim >= start),
                )
            )
        ).all()
        for row in rows:
            items.append(CockpitItem(
                tipo="promocao",
                referencia_id=row.id,
                data_referencia=row.data_inicio,
                descricao=row.nome,
                hora_inicio=row.hora_inicio,
            ))

    # Layer 3: contas_pagar (requires "financeiro" permission)
    if "financeiro" in permissions:
        rows = db.execute(
            select(
                ContaPagar.id,
                ContaPagar.data_vencimento,
                ContaPagar.valor,
                Fornecedor.nome.label("fornecedor_nome"),
            )
            .outerjoin(Fornecedor, Fornecedor.id == ContaPagar.fornecedor_id)
            .where(
                and_(
                    ContaPagar.status == "pendente",
                    ContaPagar.data_vencimento >= start,
                    ContaPagar.data_vencimento <= end,
                )
            )
        ).all()
        for row in rows:
            fnome: Optional[str] = row.fornecedor_nome
            items.append(CockpitItem(
                tipo="conta_pagar",
                referencia_id=row.id,
                data_referencia=row.data_vencimento,
                descricao=fnome or "Sem fornecedor",
                valor=Decimal(str(row.valor)),
                fornecedor_nome=fnome,
            ))

    # Layer 4: entregas agendadas (requires "estoque" permission)
    if "estoque" in permissions:
        rows = db.execute(
            select(
                Compra.id,
                Compra.data_prevista_recebimento,
                Compra.hora_prevista_recebimento,
                Fornecedor.nome.label("fornecedor_nome"),
            )
            .outerjoin(Fornecedor, Fornecedor.id == Compra.fornecedor_id)
            .where(
                and_(
                    Compra.status == "confirmado",
                    Compra.data_prevista_recebimento.isnot(None),
                    Compra.data_prevista_recebimento >= start,
                    Compra.data_prevista_recebimento <= end,
                )
            )
        ).all()
        compra_ids = [row.id for row in rows]
        itens_map: dict[int, list[str]] = {}
        if compra_ids:
            item_rows = db.execute(
                select(ItemCompra.compra_id, Insumo.nome)
                .join(Insumo, Insumo.id == ItemCompra.insumo_id)
                .where(ItemCompra.compra_id.in_(compra_ids))
                .order_by(ItemCompra.compra_id, Insumo.nome)
            ).all()
            for ir in item_rows:
                itens_map.setdefault(ir.compra_id, []).append(ir.nome)
        for row in rows:
            fnome = row.fornecedor_nome
            nomes_itens = itens_map.get(row.id, [])
            items.append(CockpitItem(
                tipo="entrega_insumo",
                referencia_id=row.id,
                data_referencia=row.data_prevista_recebimento,
                hora_inicio=row.hora_prevista_recebimento,
                descricao=fnome or "Sem fornecedor",
                fornecedor_nome=fnome,
                itens=nomes_itens,
            ))

    items.sort(key=lambda x: x.data_referencia)
    return items
