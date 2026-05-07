from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import auth as auth_routes
from src.api.routes import categorias as categorias_routes
from src.api.routes import fornecedores as fornecedores_routes
from src.api.routes import garcons as garcons_routes
from src.api.routes import health
from src.api.routes import metodos_pagamento as metodos_pagamento_routes
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
    app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])
    app.include_router(categorias_routes.router, prefix="/api/categorias", tags=["categorias"])
    app.include_router(fornecedores_routes.router, prefix="/api/fornecedores", tags=["fornecedores"])
    app.include_router(garcons_routes.router, prefix="/api/garcons", tags=["garcons"])
    app.include_router(metodos_pagamento_routes.router, prefix="/api/metodos-pagamento", tags=["metodos_pagamento"])

    log = get_logger(__name__)
    log.info("app_started", env=settings.ENV, version=settings.APP_VERSION)

    return app


app = create_app()
