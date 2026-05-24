import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from src.core.database import SessionLocal
from src.core.logging import get_logger
from src.repositories import (
    compras_repository,
    notificacoes_repository,
    refresh_tokens_repository,
    revoked_tokens_repository,
)
from src.services import contas_pagar_service

log = get_logger(__name__)

_scheduler = BackgroundScheduler()


def _verificar_entregas_previstas() -> None:
    db = SessionLocal()
    try:
        hoje = datetime.date.today()
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
        db.commit()
        log.info("scheduler_entregas_verificadas", total=len(compras))
    except Exception as e:
        log.error("scheduler_entregas_erro", error=str(e))
        db.rollback()
    finally:
        db.close()


def _atualizar_contas_vencidas() -> None:
    db = SessionLocal()
    try:
        total = contas_pagar_service.atualizar_vencidos(db)
        log.info("scheduler_contas_vencidas_atualizadas", total=total)
    except Exception as e:
        log.error("scheduler_contas_vencidas_erro", error=str(e))
    finally:
        db.close()


def _limpar_revoked_tokens() -> None:
    db = SessionLocal()
    try:
        deleted = revoked_tokens_repository.delete_expired(db)
        log.info("scheduler_revoked_tokens_limpos", total=deleted)
    except Exception as e:
        log.error("scheduler_revoked_tokens_erro", error=str(e))
    finally:
        db.close()


def _limpar_refresh_tokens() -> None:
    db = SessionLocal()
    try:
        deleted = refresh_tokens_repository.delete_expired(db)
        log.info("scheduler_refresh_tokens_limpos", total=deleted)
    except Exception as e:
        log.error("scheduler_refresh_tokens_erro", error=str(e))
    finally:
        db.close()


def start() -> None:
    _scheduler.add_job(_verificar_entregas_previstas, "cron", hour=8, minute=0, id="entregas_previstas")
    _scheduler.add_job(_atualizar_contas_vencidas, "cron", hour=8, minute=5, id="contas_vencidas")
    _scheduler.add_job(_limpar_revoked_tokens, "interval", hours=1, id="revoked_tokens_cleanup")
    _scheduler.add_job(_limpar_refresh_tokens, "cron", hour=3, minute=0, id="refresh_tokens_cleanup")
    _scheduler.start()
    log.info("scheduler_started")


def stop() -> None:
    _scheduler.shutdown(wait=False)
    log.info("scheduler_stopped")
