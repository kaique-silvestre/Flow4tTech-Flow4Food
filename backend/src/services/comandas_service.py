import datetime
import json
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.comandas import Comanda, StatusComanda
from src.models.eventos_comanda import TipoEvento
from src.models.ficha_tecnica import FichaTecnica
from src.models.insumos import Insumo
from src.models.itens_comanda import ItemComanda
from src.models.metodos_pagamento import MetodoPagamento
from src.models.movimentos_estoque import TipoMovimento
from src.models.produtos import Produto
from src.repositories import (
    comandas_repository,
    estoque_repository,
    garcons_repository,
    pagamentos_repository,
)
from src.schemas.comandas import (
    CancelarItemRequest,
    ComandaCreateRequest,
    ComandaResponse,
    EditarItemRequest,
    ItemComandaResponse,
    LancarItemRequest,
    PatchComandaRequest,
)
from src.schemas.fechamento import AplicarDescontoRequest, FecharComandaRequest, PagamentoResponse
from src.schemas.produtos import ProdutoResponse
from src.services import produtos_service


def _parse_pessoas(pessoas_json: Optional[str]) -> list[str]:
    if not pessoas_json:
        return []
    try:
        return json.loads(pessoas_json)
    except Exception:
        return []


def _build_item_response(db: Session, ic: ItemComanda) -> ItemComandaResponse:
    produto = db.execute(select(Produto).where(Produto.id == ic.produto_id)).scalar_one_or_none()
    item_nome = produto.nome if produto else f"Produto {ic.produto_id}"
    subtotal = ic.quantidade * ic.preco_unitario
    return ItemComandaResponse(
        id=ic.id,
        item_id=ic.produto_id,
        item_nome=item_nome,
        quantidade=ic.quantidade,
        preco_unitario=ic.preco_unitario,
        subtotal=subtotal,
        pessoa_associada=ic.pessoa_associada,
        observacao=ic.observacao,
        cortesia=ic.cortesia,
        cancelado=ic.cancelado,
        motivo_cancelamento=ic.motivo_cancelamento,
        estornado=ic.estornado,
        created_at=ic.created_at,
    )


def _build_response(db: Session, comanda: Comanda) -> ComandaResponse:
    garcom = garcons_repository.get_by_id(db, comanda.garcom_id)
    garcom_nome = garcom.nome if garcom else f"Garçom {comanda.garcom_id}"

    pessoas = _parse_pessoas(comanda.pessoas)
    itens = comandas_repository.get_itens_ativos(db, comanda.id)
    itens_resp = [_build_item_response(db, ic) for ic in itens]

    total_parcial = sum(
        (ir.subtotal for ir in itens_resp if not ir.cancelado),
        Decimal("0"),
    )

    now = datetime.datetime.utcnow()
    created = comanda.created_at
    if hasattr(created, "replace"):
        delta = now - created.replace(tzinfo=None)
    else:
        delta = datetime.timedelta(0)
    tempo_aberta_minutos = int(delta.total_seconds() // 60)

    pagamentos_db = pagamentos_repository.list_by_comanda(db, comanda.id)
    pagamentos_resp = []
    for p in pagamentos_db:
        metodo = db.get(MetodoPagamento, p.metodo_id)
        metodo_nome = metodo.nome if metodo else f"Método {p.metodo_id}"
        pagamentos_resp.append(
            PagamentoResponse(id=p.id, metodo_id=p.metodo_id, metodo_nome=metodo_nome, valor=p.valor)
        )

    return ComandaResponse(
        id=comanda.id,
        identificacao=comanda.identificacao,
        tipo_identificacao=comanda.tipo_identificacao,
        garcom_id=comanda.garcom_id,
        garcom_nome=garcom_nome,
        status=comanda.status,
        version=comanda.version,
        pessoas=pessoas,
        total_parcial=total_parcial,
        itens_ativos=itens_resp,
        created_at=comanda.created_at,
        tempo_aberta_minutos=tempo_aberta_minutos,
        desconto_percentual=comanda.desconto_percentual,
        desconto_valor=comanda.desconto_valor,
        total=comanda.total,
        saldo_pendente=comanda.saldo_pendente,
        data_fechamento=comanda.data_fechamento,
        pagamentos=pagamentos_resp,
    )


def abrir_comanda(db: Session, data: ComandaCreateRequest) -> ComandaResponse:
    garcom = garcons_repository.get_by_id(db, data.garcom_id)
    if garcom is None:
        raise AppError(ErrorCode.NOT_FOUND, "Garçom não encontrado", http_status=404)
    if not garcom.ativo:
        raise AppError(ErrorCode.GARCOM_INATIVO, "Garçom inativo não pode abrir comanda", http_status=400)

    comanda = comandas_repository.create_comanda(db, data)
    comandas_repository.add_evento(
        db,
        comanda.id,
        TipoEvento.COMANDA_ABERTA,
        {"identificacao": data.identificacao, "garcom_id": data.garcom_id},
        garcom_id=data.garcom_id,
    )
    db.commit()
    db.refresh(comanda)
    return _build_response(db, comanda)


def get_comanda(db: Session, comanda_id: int) -> ComandaResponse:
    comanda = comandas_repository.get_by_id(db, comanda_id)
    if comanda is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)
    return _build_response(db, comanda)


_ABERTA_STATUSES = {StatusComanda.ABERTA.value, StatusComanda.REABERTA.value}


def patch_comanda(db: Session, comanda_id: int, data: PatchComandaRequest) -> ComandaResponse:
    comanda = comandas_repository.get_by_id(db, comanda_id)
    if comanda is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)
    if comanda.status not in _ABERTA_STATUSES:
        raise AppError(ErrorCode.COMANDA_FECHADA, "Comanda não está aberta", http_status=400)

    if data.garcom_id is not None:
        garcom = garcons_repository.get_by_id(db, data.garcom_id)
        if garcom is None:
            raise AppError(ErrorCode.NOT_FOUND, "Garçom não encontrado", http_status=404)
        if not garcom.ativo:
            raise AppError(ErrorCode.GARCOM_INATIVO, "Garçom inativo", http_status=400)
        comanda.garcom_id = data.garcom_id

    if data.identificacao is not None:
        comanda.identificacao = data.identificacao

    if data.pessoas is not None:
        comanda.pessoas = json.dumps(data.pessoas, ensure_ascii=False)

    comandas_repository.add_evento(
        db,
        comanda_id,
        TipoEvento.COMANDA_EDITADA,
        {
            "identificacao": data.identificacao,
            "garcom_id": data.garcom_id,
        },
    )
    db.commit()
    db.refresh(comanda)
    return _build_response(db, comanda)


def lancar_item(db: Session, comanda_id: int, data: LancarItemRequest) -> ComandaResponse:
    comanda = comandas_repository.get_by_id(db, comanda_id)
    if comanda is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)
    if comanda.status not in _ABERTA_STATUSES:
        raise AppError(ErrorCode.COMANDA_FECHADA, "Comanda não está aberta", http_status=400)

    produto = db.execute(select(Produto).where(Produto.id == data.item_id, Produto.ativo == True)).scalar_one_or_none()  # noqa: E712
    if produto is None:
        raise AppError(ErrorCode.NOT_FOUND, "Produto não encontrado ou inativo", http_status=404)

    preco_unitario = Decimal("0") if data.cortesia else (produto.preco_venda or Decimal("0"))

    ok = comandas_repository.increment_version(db, comanda_id, data.version)
    if not ok:
        raise AppError(
            ErrorCode.COMANDA_DESATUALIZADA,
            "Comanda foi alterada por outro usuário, recarregue",
            http_status=409,
        )

    comandas_repository.add_item(
        db,
        comanda_id,
        data.item_id,
        data.quantidade,
        preco_unitario,
        data.pessoa_associada,
        data.observacao,
        data.cortesia,
    )
    comandas_repository.add_evento(
        db,
        comanda_id,
        TipoEvento.ITEM_LANCADO,
        {
            "item_id": data.item_id,
            "quantidade": str(data.quantidade),
            "cortesia": data.cortesia,
            "pessoa_associada": data.pessoa_associada,
        },
    )
    db.commit()
    comanda = comandas_repository.get_by_id(db, comanda_id)
    return _build_response(db, comanda)  # type: ignore[arg-type]


def editar_item(
    db: Session,
    comanda_id: int,
    item_comanda_id: int,
    data: EditarItemRequest,
) -> ComandaResponse:
    comanda = comandas_repository.get_by_id(db, comanda_id)
    if comanda is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)
    if comanda.status not in _ABERTA_STATUSES:
        raise AppError(ErrorCode.COMANDA_FECHADA, "Comanda não está aberta", http_status=400)

    item_c = comandas_repository.get_item(db, item_comanda_id)
    if item_c is None or item_c.comanda_id != comanda_id:
        raise AppError(ErrorCode.NOT_FOUND, "Item não encontrado nesta comanda", http_status=404)
    if item_c.cancelado:
        raise AppError(ErrorCode.NOT_FOUND, "Item já cancelado", http_status=400)

    ok = comandas_repository.increment_version(db, comanda_id, data.version)
    if not ok:
        raise AppError(
            ErrorCode.COMANDA_DESATUALIZADA,
            "Comanda foi alterada por outro usuário, recarregue",
            http_status=409,
        )

    comandas_repository.update_item(db, item_comanda_id, data.quantidade, data.pessoa_associada, data.observacao)
    comandas_repository.add_evento(
        db,
        comanda_id,
        TipoEvento.ITEM_EDITADO,
        {
            "item_comanda_id": item_comanda_id,
            "quantidade": str(data.quantidade) if data.quantidade else None,
            "pessoa_associada": data.pessoa_associada,
            "observacao": data.observacao,
        },
    )
    db.commit()
    comanda = comandas_repository.get_by_id(db, comanda_id)
    return _build_response(db, comanda)  # type: ignore[arg-type]


def cancelar_item(
    db: Session,
    comanda_id: int,
    item_comanda_id: int,
    data: CancelarItemRequest,
) -> ComandaResponse:
    comanda = comandas_repository.get_by_id(db, comanda_id)
    if comanda is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)
    if comanda.status not in _ABERTA_STATUSES:
        raise AppError(ErrorCode.COMANDA_FECHADA, "Comanda não está aberta", http_status=400)

    item_c = comandas_repository.get_item(db, item_comanda_id)
    if item_c is None or item_c.comanda_id != comanda_id:
        raise AppError(ErrorCode.NOT_FOUND, "Item não encontrado nesta comanda", http_status=404)
    if item_c.cancelado:
        raise AppError(ErrorCode.NOT_FOUND, "Item já cancelado", http_status=400)

    ok = comandas_repository.increment_version(db, comanda_id, data.version)
    if not ok:
        raise AppError(
            ErrorCode.COMANDA_DESATUALIZADA,
            "Comanda foi alterada por outro usuário, recarregue",
            http_status=409,
        )

    comandas_repository.cancelar_item(db, item_comanda_id, data.motivo.value, data.estornado)
    comandas_repository.add_evento(
        db,
        comanda_id,
        TipoEvento.ITEM_CANCELADO,
        {
            "item_comanda_id": item_comanda_id,
            "motivo": data.motivo.value,
            "estornado": data.estornado,
        },
    )
    db.commit()
    comanda = comandas_repository.get_by_id(db, comanda_id)
    return _build_response(db, comanda)  # type: ignore[arg-type]


def get_top_itens(db: Session, dias: int, limit: int) -> list[ProdutoResponse]:
    return produtos_service.get_top_produtos(db, dias, limit)


def aplicar_desconto(db: Session, comanda_id: int, data: AplicarDescontoRequest) -> ComandaResponse:
    comanda = comandas_repository.get_by_id(db, comanda_id)
    if comanda is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)
    if comanda.status not in _ABERTA_STATUSES:
        raise AppError(ErrorCode.COMANDA_FECHADA, "Comanda não está aberta", http_status=400)

    comandas_repository.atualizar_desconto(db, comanda_id, data.desconto_percentual, data.desconto_valor)
    db.commit()
    db.refresh(comanda)
    return _build_response(db, comanda)


def fechar_comanda(db: Session, comanda_id: int, data: FecharComandaRequest) -> ComandaResponse:
    comanda = comandas_repository.get_by_id(db, comanda_id)
    if comanda is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)
    if comanda.status not in _ABERTA_STATUSES:
        raise AppError(ErrorCode.COMANDA_FECHADA, "Comanda não está aberta", http_status=400)

    if data.modo_divisao == "por_pessoa":
        pessoas = _parse_pessoas(comanda.pessoas)
        if len(pessoas) < 2:
            raise AppError(
                ErrorCode.PESSOAS_INSUFICIENTES,
                "Divisão por pessoa exige ao menos 2 pessoas cadastradas na comanda",
                http_status=400,
            )

    itens = comandas_repository.get_itens_para_fechar(db, comanda_id)
    subtotal: Decimal = sum((ic.preco_unitario * ic.quantidade for ic in itens), Decimal("0"))

    total_pago: Decimal = sum((p.valor for p in data.pagamentos), Decimal("0"))
    pagamento_parcial = data.modo_divisao == "parcial"

    if comanda.desconto_percentual is not None:
        total_com_desconto: Decimal = subtotal * (Decimal("1") - comanda.desconto_percentual / Decimal("100"))
    elif comanda.desconto_valor is not None:
        total_com_desconto = subtotal - comanda.desconto_valor
    else:
        total_com_desconto = subtotal

    if pagamento_parcial:
        base_parcial: Decimal = comanda.saldo_pendente if comanda.saldo_pendente is not None else subtotal
        if total_pago >= base_parcial:
            raise AppError(
                ErrorCode.PAGAMENTO_NAO_BATE,
                "Pagamento parcial deve ser menor que o total",
                http_status=400,
            )
    else:
        base_total: Decimal = comanda.saldo_pendente if comanda.saldo_pendente is not None else total_com_desconto
        if abs(total_pago - base_total) > Decimal("0.01"):
            raise AppError(
                ErrorCode.PAGAMENTO_NAO_BATE,
                f"Soma dos pagamentos (R$ {total_pago}) nao confere com o total (R$ {base_total})",
                http_status=400,
            )

    for p in data.pagamentos:
        metodo = db.get(MetodoPagamento, p.metodo_id)
        if metodo is None:
            raise AppError(ErrorCode.NOT_FOUND, f"Metodo de pagamento {p.metodo_id} nao encontrado", http_status=404)
        pagamentos_repository.create_pagamento(db, comanda_id, p.metodo_id, p.valor)

    itens_negativos: list[str] = []

    if pagamento_parcial:
        novo_saldo: Decimal = base_parcial - total_pago
        comandas_repository.atualizar_saldo_pendente(db, comanda_id, novo_saldo)
    else:
        for ic in itens:
            negativos = _dar_baixa_estoque(db, ic.produto_id, ic.quantidade)
            itens_negativos.extend(negativos)
        comandas_repository.fechar_comanda_repo(db, comanda_id, total_com_desconto)

    db.commit()
    db.refresh(comanda)
    response = _build_response(db, comanda)
    response.itens_negativos = itens_negativos
    return response


def _dar_baixa_estoque(db: Session, produto_id: int, quantidade: Decimal) -> list[str]:
    componentes = db.execute(
        select(FichaTecnica).where(FichaTecnica.produto_id == produto_id)
    ).scalars().all()
    if not componentes:
        return []
    negativos: list[str] = []
    for comp in componentes:
        insumo = db.execute(select(Insumo).where(Insumo.id == comp.insumo_id)).scalar_one_or_none()
        if insumo:
            negativos.extend(_baixar_insumo(db, insumo, comp.quantidade * quantidade))
    return negativos


def _baixar_insumo(db: Session, insumo: Insumo, quantidade: Decimal) -> list[str]:
    novo_estoque = insumo.estoque_atual - quantidade
    insumo.estoque_atual = novo_estoque
    estoque_repository.registrar_movimento(
        db,
        insumo_id=insumo.id,
        tipo=TipoMovimento.SAIDA_VENDA,
        quantidade=quantidade,
        custo_unitario=insumo.custo_medio,
        saldo_apos=novo_estoque,
    )
    db.flush()
    return [insumo.nome] if novo_estoque < 0 else []


def reabrir_comanda(db: Session, comanda_id: int) -> ComandaResponse:
    comanda = comandas_repository.get_by_id(db, comanda_id)
    if comanda is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)
    if comanda.status != StatusComanda.FECHADA.value:
        raise AppError(
            ErrorCode.COMANDA_NAO_FECHADA,
            "Apenas comandas fechadas podem ser reabertas",
            http_status=400,
        )

    itens = comandas_repository.get_itens_para_fechar(db, comanda_id)
    for ic in itens:
        _estornar_estoque(db, ic.produto_id, ic.quantidade)

    comandas_repository.reabrir_comanda_repo(db, comanda_id)
    comandas_repository.add_evento(
        db, comanda_id, TipoEvento.COMANDA_REABERTA, {}, comanda.garcom_id
    )

    db.commit()
    db.refresh(comanda)
    return _build_response(db, comanda)


def _estornar_estoque(db: Session, produto_id: int, quantidade: Decimal) -> None:
    componentes = db.execute(
        select(FichaTecnica).where(FichaTecnica.produto_id == produto_id)
    ).scalars().all()
    for comp in componentes:
        insumo = db.execute(select(Insumo).where(Insumo.id == comp.insumo_id)).scalar_one_or_none()
        if insumo is not None:
            _estornar_insumo(db, insumo, comp.quantidade * quantidade)


def _estornar_insumo(db: Session, insumo: Insumo, quantidade: Decimal) -> None:
    novo_estoque = insumo.estoque_atual + quantidade
    insumo.estoque_atual = novo_estoque
    estoque_repository.registrar_movimento(
        db,
        insumo_id=insumo.id,
        tipo=TipoMovimento.ENTRADA_ESTORNO,
        quantidade=quantidade,
        custo_unitario=insumo.custo_medio,
        saldo_apos=novo_estoque,
    )
    db.flush()
