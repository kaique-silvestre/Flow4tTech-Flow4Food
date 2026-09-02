from enum import Enum
from typing import Any, Optional

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
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
    CONFLICT = "CONFLICT"
    FORBIDDEN = "FORBIDDEN"
    CAIXA_JA_FECHADO = "CAIXA_JA_FECHADO"


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


_STATUS_CODE_MAP: dict[int, ErrorCode] = {
    401: ErrorCode.UNAUTHORIZED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.NOT_FOUND,
    409: ErrorCode.CONFLICT,
}


def _code_for_status(status_code: int) -> ErrorCode:
    return _STATUS_CODE_MAP.get(status_code, ErrorCode.VALIDATION_ERROR)


def _error_field_path(error: dict[str, Any]) -> str:
    return ".".join(str(part) for part in error.get("loc", ()) if part != "body")


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
        # A dict detail is a structured payload raised deliberately (e.g. the
        # SUBSCRIPTION_BLOCKED block in dependencies.py) — preserve it as-is,
        # matching FastAPI's default {"detail": ...} shape the frontend expects,
        # instead of collapsing it to a string.
        if isinstance(exc.detail, dict):
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        code = _code_for_status(exc.status_code)
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(code.value, str(exc.detail), None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        field_paths = [_error_field_path(e) for e in errors]
        message = (
            "; ".join(f"{path}: {e.get('msg')}" for path, e in zip(field_paths, errors))
            or "Erro de validação"
        )
        field = (field_paths[0] or None) if field_paths else None
        return JSONResponse(
            status_code=422,
            content=_payload(ErrorCode.VALIDATION_ERROR.value, message, field),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        log.error("unhandled_exception", exc_info=exc)
        sentry_sdk.capture_exception(exc)
        return JSONResponse(
            status_code=500,
            content=_payload(ErrorCode.INTERNAL_ERROR.value, "Erro interno do servidor", None),
        )
