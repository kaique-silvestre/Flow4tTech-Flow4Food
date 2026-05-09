from enum import Enum
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.logging import get_logger

log = get_logger(__name__)


class ErrorCode(str, Enum):
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    SENHA_INCORRETA = "SENHA_INCORRETA"
    COMANDA_FECHADA = "COMANDA_FECHADA"
    COMANDA_DESATUALIZADA = "COMANDA_DESATUALIZADA"
    GARCOM_INATIVO = "GARCOM_INATIVO"
    PAGAMENTO_NAO_BATE = "PAGAMENTO_NAO_BATE"
    PESSOAS_INSUFICIENTES = "PESSOAS_INSUFICIENTES"
    FICHA_VAZIA = "FICHA_VAZIA"
    PRECO_EM_NAO_VENDAVEL = "PRECO_EM_NAO_VENDAVEL"
    FICHA_ANINHADA_NAO_SUPORTADA = "FICHA_ANINHADA_NAO_SUPORTADA"
    COMANDA_NAO_FECHADA = "COMANDA_NAO_FECHADA"
    HAS_CHILDREN = "HAS_CHILDREN"
    NIVEL_MAX_ATINGIDO = "NIVEL_MAX_ATINGIDO"


class AppError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        field: Optional[str] = None,
        http_status: int = 400,
    ) -> None:
        self.code = code
        self.message = message
        self.field = field
        self.http_status = http_status
        super().__init__(message)


def _payload(code: str, message: str, field: Optional[str]) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "field": field}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content=_payload(exc.code.value, exc.message, exc.field),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code = ErrorCode.NOT_FOUND if exc.status_code == 404 else ErrorCode.VALIDATION_ERROR
        if exc.status_code == 401:
            code = ErrorCode.UNAUTHORIZED
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(code.value, str(exc.detail), None),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        log.error("unhandled_exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=_payload(ErrorCode.INTERNAL_ERROR.value, "Erro interno do servidor", None),
        )
