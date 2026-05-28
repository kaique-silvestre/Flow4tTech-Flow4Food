from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_tenant_db, require_permission
from src.schemas.caixa import (
    AbrirCaixaRequest,
    CaixaMovimentoResponse,
    CaixaSessaoResponse,
    FecharCaixaRequest,
    MovimentoCaixaRequest,
)
from src.services import caixa_service

router = APIRouter(dependencies=[Depends(require_permission("caixa"))])


@router.post("/abrir", response_model=CaixaSessaoResponse, status_code=201)
def abrir_caixa(
    body: AbrirCaixaRequest,
    payload: dict = Depends(require_permission("caixa")),
    db: Session = Depends(get_tenant_db),
) -> CaixaSessaoResponse:
    user_id: int = payload["user_id"]
    return caixa_service.abrir_caixa(db, body, user_id)


@router.post("/fechar", response_model=CaixaSessaoResponse)
def fechar_caixa(
    body: FecharCaixaRequest,
    payload: dict = Depends(require_permission("caixa")),
    db: Session = Depends(get_tenant_db),
) -> CaixaSessaoResponse:
    user_id: int = payload["user_id"]
    return caixa_service.fechar_caixa(db, body, user_id)


@router.post("/movimentos", response_model=CaixaMovimentoResponse, status_code=201)
def registrar_movimento(
    body: MovimentoCaixaRequest,
    payload: dict = Depends(require_permission("caixa")),
    db: Session = Depends(get_tenant_db),
) -> CaixaMovimentoResponse:
    user_id: int = payload["user_id"]
    return caixa_service.registrar_movimento(db, body, user_id)


@router.get("/sessao", response_model=CaixaSessaoResponse)
def get_sessao_aberta(
    db: Session = Depends(get_tenant_db),
) -> CaixaSessaoResponse:
    return caixa_service.get_sessao_aberta(db)
