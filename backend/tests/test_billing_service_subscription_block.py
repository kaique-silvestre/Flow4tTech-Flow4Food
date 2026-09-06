"""Unit tests for billing_service.evaluate_subscription_block — the pure
blocked/allowed decision extracted out of api/dependencies.check_subscription
(dependencies.py stays responsible only for the DB fetch + HTTPException,
since that part is tightly coupled to FastAPI's Depends chain)."""
import datetime
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

from src.services import billing_service


def test_ativa_is_not_blocked():
    assert billing_service.evaluate_subscription_block("ativa", None) is None


def test_trial_sem_vencimento_is_not_blocked():
    assert billing_service.evaluate_subscription_block("trial", None) is None


def test_trial_vencimento_futuro_is_not_blocked():
    future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=5)
    assert billing_service.evaluate_subscription_block("trial", future) is None


def test_trial_vencimento_passado_is_blocked():
    past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    block = billing_service.evaluate_subscription_block("trial", past)
    assert block == {"status": "trial"}


def test_suspensa_is_blocked():
    assert billing_service.evaluate_subscription_block("suspensa", None) == {"status": "suspensa"}


def test_cancelada_is_blocked():
    assert billing_service.evaluate_subscription_block("cancelada", None) == {"status": "cancelada"}


def test_naive_data_vencimento_is_treated_as_utc():
    """data_vencimento sem tzinfo (SQLite/legacy rows) não deve estourar TypeError."""
    naive_past = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - datetime.timedelta(days=1)
    block = billing_service.evaluate_subscription_block("trial", naive_past)
    assert block == {"status": "trial"}
