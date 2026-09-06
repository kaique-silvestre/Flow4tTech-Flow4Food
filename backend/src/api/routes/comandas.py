import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_tenant_db, require_feature, require_permission
from src.schemas.comandas import (
    CancelarComandaRequest,
    CancelarItemRequest,
    ComandaCreateRequest,
    ComandaResponse,
    EditarItemRequest,
    LancarItemRequest,
    PatchComandaRequest,
    ReabrirComandaRequest,
)
from src.schemas.comprovante import ComprovanteResponse
from src.schemas.fechamento import AplicarDescontoRequest, FecharComandaRequest
from src.services import audit_service, comandas_service, comprovante_service

router = APIRouter(dependencies=[Depends(require_feature("comandas")), Depends(require_permission("comandas"))])


@router.post("", response_model=ComandaResponse, status_code=201)
def abrir_comanda(
    body: ComandaCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(get_current_user),
) -> ComandaResponse:
    result = comandas_service.abrir_comanda(db, body)  # type: ignore[return-value]
    background_tasks.add_task(
        audit_service.log_background,
        "comanda.abrir",
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
        entity="Comanda",
        entity_id=result.id,
        after={"identificacao": body.identificacao, "garcom_id": body.garcom_id},
        impersonated_by=payload.get("impersonated_by"),
    )
    return result


@router.get("/fechadas", response_model=list[ComandaResponse])
def list_fechadas(
    busca: Optional[str] = Query(None),
    data_inicio: Optional[datetime.date] = Query(None),
    data_fim: Optional[datetime.date] = Query(None),
    db: Session = Depends(get_tenant_db),
) -> list[ComandaResponse]:
    return comandas_service.list_comandas_fechadas(db, busca, data_inicio, data_fim)  # type: ignore[return-value]


@router.get("/count-abertas", response_model=int)
def count_abertas(
    db: Session = Depends(get_tenant_db),
) -> int:
    from src.repositories import comandas_repository
    return comandas_repository.count_abertas(db)


@router.get("", response_model=list[ComandaResponse])
def list_comandas(
    busca: Optional[str] = Query(None),
    db: Session = Depends(get_tenant_db),
) -> list[ComandaResponse]:
    return comandas_service.list_comandas_abertas(db, busca)  # type: ignore[return-value]


@router.patch("/{comanda_id}", response_model=ComandaResponse)
def patch_comanda(
    comanda_id: int,
    body: PatchComandaRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(get_current_user),
) -> ComandaResponse:
    result = comandas_service.patch_comanda(db, comanda_id, body)  # type: ignore[return-value]
    background_tasks.add_task(
        audit_service.log_background,
        "comanda.patch",
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
        entity="Comanda",
        entity_id=comanda_id,
        after={"identificacao": body.identificacao, "garcom_id": body.garcom_id},
        impersonated_by=payload.get("impersonated_by"),
    )
    return result


@router.get("/{comanda_id}", response_model=ComandaResponse)
def get_comanda(
    comanda_id: int,
    db: Session = Depends(get_tenant_db),
) -> ComandaResponse:
    return comandas_service.get_comanda(db, comanda_id)  # type: ignore[return-value]


@router.post("/{comanda_id}/itens", response_model=ComandaResponse)
def lancar_item(
    comanda_id: int,
    body: LancarItemRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(get_current_user),
) -> ComandaResponse:
    result = comandas_service.lancar_item(db, comanda_id, body)  # type: ignore[return-value]
    background_tasks.add_task(
        audit_service.log_background,
        "comanda.item.lancar",
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
        entity="Comanda",
        entity_id=comanda_id,
        after={"item_id": body.item_id, "quantidade": str(body.quantidade)},
        impersonated_by=payload.get("impersonated_by"),
    )
    return result


@router.patch("/{comanda_id}/itens/{item_id}", response_model=ComandaResponse)
def editar_item(
    comanda_id: int,
    item_id: int,
    body: EditarItemRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(get_current_user),
) -> ComandaResponse:
    result = comandas_service.editar_item(db, comanda_id, item_id, body)  # type: ignore[return-value]
    background_tasks.add_task(
        audit_service.log_background,
        "comanda.item.editar",
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
        entity="ComandaItem",
        entity_id=item_id,
        after={
            "quantidade": str(body.quantidade) if body.quantidade is not None else None,
            "pessoa_associada": body.pessoa_associada,
            "observacao": body.observacao,
        },
        impersonated_by=payload.get("impersonated_by"),
    )
    return result


@router.post("/{comanda_id}/itens/{item_id}/cancelar", response_model=ComandaResponse)
def cancelar_item(
    comanda_id: int,
    item_id: int,
    body: CancelarItemRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(get_current_user),
) -> ComandaResponse:
    result = comandas_service.cancelar_item(db, comanda_id, item_id, body)  # type: ignore[return-value]
    background_tasks.add_task(
        audit_service.log_background,
        "comanda.item.cancelar",
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
        entity="ComandaItem",
        entity_id=item_id,
        impersonated_by=payload.get("impersonated_by"),
    )
    return result


@router.post("/{comanda_id}/desconto", response_model=ComandaResponse)
def aplicar_desconto(
    comanda_id: int,
    body: AplicarDescontoRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(get_current_user),
) -> ComandaResponse:
    result = comandas_service.aplicar_desconto(db, comanda_id, body)  # type: ignore[return-value]
    background_tasks.add_task(
        audit_service.log_background,
        "comanda.desconto",
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
        entity="Comanda",
        entity_id=comanda_id,
        after={
            "desconto_valor": str(body.desconto_valor) if body.desconto_valor is not None else None,
            "desconto_percentual": str(body.desconto_percentual)
            if body.desconto_percentual is not None
            else None,
        },
        impersonated_by=payload.get("impersonated_by"),
    )
    return result


@router.post("/{comanda_id}/fechar", response_model=ComandaResponse)
def fechar_comanda(
    comanda_id: int,
    body: FecharComandaRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(get_current_user),
) -> ComandaResponse:
    result = comandas_service.fechar_comanda(db, comanda_id, body)  # type: ignore[return-value]
    background_tasks.add_task(
        audit_service.log_background,
        "comanda.fechar",
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
        entity="Comanda",
        entity_id=comanda_id,
        after={"modo_divisao": body.modo_divisao, "taxa_servico": body.taxa_servico},
        impersonated_by=payload.get("impersonated_by"),
    )
    return result


@router.post("/{comanda_id}/reabrir", response_model=ComandaResponse)
def reabrir_comanda(
    comanda_id: int,
    body: ReabrirComandaRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(get_current_user),
) -> ComandaResponse:
    result = comandas_service.reabrir_comanda(db, comanda_id, body)  # type: ignore[return-value]
    background_tasks.add_task(
        audit_service.log_background,
        "comanda.reabrir",
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
        entity="Comanda",
        entity_id=comanda_id,
        impersonated_by=payload.get("impersonated_by"),
    )
    return result


@router.post("/{comanda_id}/cancelar", response_model=ComandaResponse)
def cancelar_comanda(
    comanda_id: int,
    body: CancelarComandaRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(get_current_user),
) -> ComandaResponse:
    result = comandas_service.cancelar_comanda(db, comanda_id, body)  # type: ignore[return-value]
    background_tasks.add_task(
        audit_service.log_background,
        "comanda.cancelar",
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
        entity="Comanda",
        entity_id=comanda_id,
        impersonated_by=payload.get("impersonated_by"),
    )
    return result


@router.get("/{comanda_id}/comprovante", response_model=ComprovanteResponse)
def get_comprovante(
    comanda_id: int,
    db: Session = Depends(get_tenant_db),
) -> ComprovanteResponse:
    return comprovante_service.build_comprovante(db, comanda_id)  # type: ignore[return-value]
