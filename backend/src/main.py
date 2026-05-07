from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import health
from src.core.config import get_settings
from src.core.errors import register_exception_handlers
from src.core.logging import configure_logging, get_logger
from src.core.middleware import RequestIdMiddleware
from src.core.sentry import init_sentry


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.ENV)
    init_sentry(settings.SENTRY_DSN_BACKEND, settings.ENV)

    app = FastAPI(
        title="Matchpoint API",
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.ENV != "prod" else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)

    register_exception_handlers(app)

    app.include_router(health.router)

    log = get_logger(__name__)
    log.info("app_started", env=settings.ENV, version=settings.APP_VERSION)

    return app


app = create_app()
