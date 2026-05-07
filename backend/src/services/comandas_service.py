import datetime
import json
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.comandas import Comanda, StatusComanda
from src.models.eventos_comanda import TipoEvento
from src.models.itens_comanda import ItemComanda
from src.repositories import comandas_repository, garcons_repository, itens_repository
from src.schemas.comandas import (
    CancelarItemRequest,
    ComandaCreateRequest,
    ComandaResponse,
    EditarItemRequest,
    ItemComandaResponse,
    LancarItemRequest,
)
from src.schemas.itens import ItemResponse
from src.services import itens_service


def _parse_pessoas(pessoas_json: Optional[str]) -> list[str]:
    if not pessoas_json:
        return []
    try:
        return json.loads(pessoas_json)
    except Exception:
        return []


def _build_item_response(db: Session, ic: ItemComanda) -> ItemComandaResponse:
    item = itens_repository.get_by_id(db, ic.item_id)
    item_nome = item.nome if item else f"Item {ic.item_id}"
    subtotal = ic.quantidade * ic.preco_unitario
    return ItemComandaResponse(
        id=ic.id,
        item_id=ic.item_id,
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


def lancar_item(db: Session, comanda_id: int, data: LancarItemRequest) -> ComandaResponse:
    comanda = comandas_repository.get_by_id(db, comanda_id)
    if comanda is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)
    if comanda.status != StatusComanda.ABERTA.value:
        raise AppError(ErrorCode.COMANDA_FECHADA, "Comanda não está aberta", http_status=400)

    item = itens_repository.get_by_id(db, data.item_id)
    if item is None or not item.vendavel:
        raise AppError(ErrorCode.NOT_FOUND, "Item não encontrado ou não vendável", http_status=404)

    preco_unitario = Decimal("0") if data.cortesia else (item.preco_venda or Decimal("0"))

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
    if comanda.status != StatusComanda.ABERTA.value:
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
    if comanda.status != StatusComanda.ABERTA.value:
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


def get_top_itens(db: Session, dias: int, limit: int) -> list[ItemResponse]:
    rows = comandas_repository.top_itens(db, dias, limit)
    result = []
    for item_id, _cnt in rows:
        item = itens_repository.get_by_id(db, item_id)
        if item:
            result.append(itens_service._build_response(db, item))
    return result
