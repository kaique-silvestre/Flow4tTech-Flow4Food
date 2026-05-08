from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.itens_comanda import ItemComanda
from src.models.metodos_pagamento import MetodoPagamento
from src.repositories import (
    comandas_repository,
    estabelecimento_repository,
    garcons_repository,
    pagamentos_repository,
)
from src.schemas.comprovante import (
    ComprovanteResponse,
    EstabelecimentoInfo,
    ItemComprovanteRow,
    PagamentoComprovanteRow,
)


def build_comprovante(db: Session, comanda_id: int) -> ComprovanteResponse:
    comanda = comandas_repository.get_by_id(db, comanda_id)
    if comanda is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)

    estab = estabelecimento_repository.get_estabelecimento(db)
    estab_info = EstabelecimentoInfo(
        nome=estab.nome if estab else "Estabelecimento",
        cnpj=estab.cnpj if estab else None,
        endereco=estab.endereco if estab else None,
        telefone=estab.telefone if estab else None,
    )

    itens_db = db.execute(
        select(ItemComanda)
        .where(ItemComanda.comanda_id == comanda_id)
        .where(ItemComanda.cancelado.is_(False))
        .order_by(ItemComanda.id)
    ).scalars().all()

    itens_rows = [
        ItemComprovanteRow(
            nome=_get_item_nome(db, ic),
            quantidade=ic.quantidade,
            preco_unitario=ic.preco_unitario,
            subtotal=ic.quantidade * ic.preco_unitario,
            cortesia=ic.cortesia,
        )
        for ic in itens_db
    ]
    subtotal = sum((r.subtotal for r in itens_rows), Decimal("0"))

    pagamentos_db = pagamentos_repository.list_by_comanda(db, comanda_id)
    pagamentos_rows = [
        PagamentoComprovanteRow(
            metodo_nome=_get_metodo_nome(db, p.metodo_id),
            valor=p.valor,
        )
        for p in pagamentos_db
    ]

    garcom = garcons_repository.get_by_id(db, comanda.garcom_id)
    garcom_nome = garcom.nome if garcom else "—"

    return ComprovanteResponse(
        comanda_id=comanda.id,
        identificacao=comanda.identificacao,
        tipo_identificacao=comanda.tipo_identificacao,
        garcom_nome=garcom_nome,
        data_fechamento=comanda.data_fechamento,
        estabelecimento=estab_info,
        itens=itens_rows,
        subtotal=subtotal,
        desconto_percentual=comanda.desconto_percentual,
        desconto_valor=comanda.desconto_valor,
        total=comanda.total,
        pagamentos=pagamentos_rows,
    )


def _get_item_nome(db: Session, ic: ItemComanda) -> str:
    from src.repositories import itens_repository
    item = itens_repository.get_by_id(db, ic.item_id)
    return item.nome if item else f"Item {ic.item_id}"


def _get_metodo_nome(db: Session, metodo_id: int) -> str:
    metodo = db.get(MetodoPagamento, metodo_id)
    return metodo.nome if metodo else f"Método {metodo_id}"
