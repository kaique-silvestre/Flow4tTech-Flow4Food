"""Tests for backend/src/core/errors.py exception handlers.

Uses a real FastAPI app with register_exception_handlers() wired up (not a bare
FastAPI() left unregistered) so the tests exercise production behavior — a
previous version of test_issue28_subscription_blocking.py used an unregistered
app and masked bug #1 below.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from src.core.errors import AppError, ErrorCode, register_exception_handlers


class _Body(BaseModel):
    nome: str
    idade: int


def _make_app() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/subscription-blocked")
    def _subscription_blocked():
        raise HTTPException(
            status_code=402,
            detail={"code": "SUBSCRIPTION_BLOCKED", "status": "suspensa", "contact": "a@b.com"},
        )

    @app.get("/forbidden")
    def _forbidden():
        raise HTTPException(status_code=403, detail="Sem permissão")

    @app.get("/conflict")
    def _conflict():
        raise HTTPException(status_code=409, detail="Já existe")

    @app.get("/not-found")
    def _not_found():
        raise HTTPException(status_code=404, detail="Não encontrado")

    @app.get("/unauthorized")
    def _unauthorized():
        raise HTTPException(status_code=401, detail="Não autenticado")

    @app.get("/boom")
    def _boom():
        raise AttributeError("kaboom")

    @app.post("/validate")
    def _validate(body: _Body):
        return {"ok": True}

    @app.get("/app-error")
    def _app_error():
        raise AppError(ErrorCode.PAGAMENTO_NAO_BATE, "Não bate", field="valor", http_status=400)

    return TestClient(app, raise_server_exceptions=False)


# 1. Structured dict detail must be preserved, not stringified.
def test_dict_detail_is_preserved_not_stringified():
    c = _make_app()
    resp = c.get("/subscription-blocked")
    assert resp.status_code == 402
    body = resp.json()
    assert body["detail"]["code"] == "SUBSCRIPTION_BLOCKED"
    assert body["detail"]["status"] == "suspensa"
    assert body["detail"]["contact"] == "a@b.com"


# 2. Status code -> ErrorCode mapping.
def test_403_maps_to_forbidden():
    c = _make_app()
    resp = c.get("/forbidden")
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == ErrorCode.FORBIDDEN.value


def test_409_maps_to_conflict():
    c = _make_app()
    resp = c.get("/conflict")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == ErrorCode.CONFLICT.value


def test_404_maps_to_not_found():
    c = _make_app()
    resp = c.get("/not-found")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == ErrorCode.NOT_FOUND.value


def test_401_maps_to_unauthorized():
    c = _make_app()
    resp = c.get("/unauthorized")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == ErrorCode.UNAUTHORIZED.value


# 3. Unhandled exceptions must be reported to Sentry explicitly.
def test_unhandled_exception_calls_sentry_capture():
    c = _make_app()
    with patch("src.core.errors.sentry_sdk.capture_exception") as mock_capture:
        resp = c.get("/boom")
    assert resp.status_code == 500
    mock_capture.assert_called_once()
    assert isinstance(mock_capture.call_args[0][0], AttributeError)


# 4. RequestValidationError uses the same envelope as the rest of the API.
def test_validation_error_uses_api_envelope():
    c = _make_app()
    resp = c.post("/validate", json={"nome": "x"})  # missing "idade"
    assert resp.status_code == 422
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == ErrorCode.VALIDATION_ERROR.value
    assert "idade" in body["error"]["field"]
    assert "idade" in body["error"]["message"]


def test_app_error_still_uses_error_envelope():
    c = _make_app()
    resp = c.get("/app-error")
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == ErrorCode.PAGAMENTO_NAO_BATE.value
    assert body["error"]["field"] == "valor"
