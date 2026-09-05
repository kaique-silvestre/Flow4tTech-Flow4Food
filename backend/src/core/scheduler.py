import datetime
from contextlib import suppress

import sentry_sdk
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, JobExecutionEvent
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text

from src.core.database import (
    SchedulerSessionLocal,
    clear_tenant_rls_context,
    set_tenant_rls_context,
)
from src.core.logging import get_logger
from src.repositories import (
    compras_repository,
    notificacoes_repository,
    refresh_tokens_repository,
    revoked_tokens_repository,
)
from src.services import billing_service, contas_pagar_service

log = get_logger(__name__)

_scheduler = BackgroundScheduler()


def _log_job_outcome(event: JobExecutionEvent) -> None:
    """Expose every scheduled execution and report failures to Sentry."""
    if event.exception is not None:
        log.error(
            "scheduler_job_failed",
            job_id=event.job_id,
            error_type=type(event.exception).__name__,
            exc_info=(type(event.exception), event.exception, event.traceback),
        )
        sentry_sdk.capture_exception(event.exception)
        return
    log.info("scheduler_job_completed", job_id=event.job_id)


def _tenant_ids(db) -> list[int]:
    """Return active tenant IDs. tenants table has no RLS — always accessible."""
    rows = db.execute(text("SELECT id FROM tenants WHERE status = 'ativo'")).fetchall()
    return [r[0] for r in rows]


def _set_tenant_context(db, tenant_id: int) -> None:
    set_tenant_rls_context(db, tenant_id)


def _clear_tenant_context(db) -> None:
    clear_tenant_rls_context(db)


def _verificar_entregas_previstas() -> None:
    db = SchedulerSessionLocal()
    try:
        hoje = datetime.date.today()
        total_compras = 0
        try:
            for tid in _tenant_ids(db):
                _set_tenant_context(db, tid)
                compras = compras_repository.list_confirmadas_com_entrega_prevista(db, hoje)
                for compra in compras:
                    if notificacoes_repository.notificacao_existe(db, "entrega_prevista", compra.id):
                        continue
                    notificacoes_repository.criar_notificacao(
                        db=db,
                        tipo="entrega_prevista",
                        mensagem=f"Compra #{str(compra.id).zfill(4)} com entrega prevista para {compra.data_prevista_recebimento} aguarda confirmação de recebimento.",
                        referencia_id=compra.id,
                    )
                total_compras += len(compras)
                db.commit()
        finally:
            # Guarantee RLS context cleanup even if the loop above raises partway
            # through, so a failed job never leaves the session's role/tenant_id
            # set for whoever reuses this connection from the pool.
            with suppress(Exception):
                db.rollback()
            try:
                _clear_tenant_context(db)
            except Exception:
                log.warning("scheduler_entregas_rls_cleanup_failed", exc_info=True)
        log.info("scheduler_entregas_verificadas", total=total_compras)
    except Exception as e:
        log.error("scheduler_entregas_erro", error=str(e))
        db.rollback()
    finally:
        db.close()


def _atualizar_contas_vencidas() -> None:
    db = SchedulerSessionLocal()
    try:
        total = 0
        try:
            for tid in _tenant_ids(db):
                _set_tenant_context(db, tid)
                total += contas_pagar_service.atualizar_vencidos(db)
        finally:
            # Guarantee RLS context cleanup even if the loop above raises partway
            # through, so a failed job never leaves the session's role/tenant_id
            # set for whoever reuses this connection from the pool.
            with suppress(Exception):
                db.rollback()
            try:
                _clear_tenant_context(db)
            except Exception:
                log.warning("scheduler_contas_vencidas_rls_cleanup_failed", exc_info=True)
        log.info("scheduler_contas_vencidas_atualizadas", total=total)
    except Exception as e:
        log.error("scheduler_contas_vencidas_erro", error=str(e))
    finally:
        db.close()


def _limpar_revoked_tokens() -> None:
    db = SchedulerSessionLocal()
    try:
        deleted = revoked_tokens_repository.delete_expired(db)
        log.info("scheduler_revoked_tokens_limpos", total=deleted)
    except Exception as e:
        log.error("scheduler_revoked_tokens_erro", error=str(e))
    finally:
        db.close()


def _limpar_refresh_tokens() -> None:
    db = SchedulerSessionLocal()
    try:
        deleted = refresh_tokens_repository.delete_expired(db)
        log.info("scheduler_refresh_tokens_limpos", total=deleted)
    except Exception as e:
        log.error("scheduler_refresh_tokens_erro", error=str(e))
    finally:
        db.close()


def _marcar_assinaturas_vencidas() -> None:
    db = SchedulerSessionLocal()
    try:
        total = billing_service.marcar_assinaturas_vencidas(db)
        log.info("scheduler_assinaturas_vencidas", total=total)
    except Exception as e:
        log.error("scheduler_assinaturas_vencidas_erro", error=str(e))
    finally:
        db.close()


def start() -> None:
    _scheduler.add_listener(_log_job_outcome, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)
    _scheduler.add_job(_verificar_entregas_previstas, "cron", hour=8, minute=0, id="entregas_previstas")
    _scheduler.add_job(_atualizar_contas_vencidas, "cron", hour=8, minute=5, id="contas_vencidas")
    _scheduler.add_job(_limpar_revoked_tokens, "interval", hours=1, id="revoked_tokens_cleanup")
    _scheduler.add_job(_limpar_refresh_tokens, "cron", hour=3, minute=0, id="refresh_tokens_cleanup")
    _scheduler.add_job(_marcar_assinaturas_vencidas, "cron", hour=0, minute=30, id="assinaturas_vencidas")
    _scheduler.start()
    log.info("scheduler_started")


def stop() -> None:
    _scheduler.shutdown(wait=False)
    log.info("scheduler_stopped")
