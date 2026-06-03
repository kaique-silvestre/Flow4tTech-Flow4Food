from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.api.routes import admin as admin_routes
from src.api.routes import auth as auth_routes
from src.api.routes import backup as backup_routes
from src.api.routes import caixa as caixa_routes
from src.api.routes import categorias as categorias_routes
from src.api.routes import comandas as comandas_routes
from src.api.routes import compras as compras_routes
from src.api.routes import config as config_routes
from src.api.routes import contas_pagar as contas_pagar_routes
from src.api.routes import dashboard as dashboard_routes
from src.api.routes import estoque as estoque_routes
from src.api.routes import fornecedores as fornecedores_routes
from src.api.routes import garcons as garcons_routes
from src.api.routes import health
from src.api.routes import insumos as insumos_routes
from src.api.routes import itens as itens_routes
from src.api.routes import metodos_pagamento as metodos_pagamento_routes
from src.api.routes import produtos as produtos_routes
from src.api.routes import profiles as profiles_routes
from src.api.routes import relatorios as relatorios_routes
from src.api.routes import users as users_routes
from src.core.config import get_settings
from src.core.errors import register_exception_handlers
from src.core.limiter import limiter
from src.core.logging import configure_logging, get_logger
from src.core.middleware import RequestIdMiddleware
from src.core.scheduler import start as scheduler_start
from src.core.scheduler import stop as scheduler_stop
from src.core.sentry import init_sentry


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    scheduler_start()
    yield
    scheduler_stop()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.ENV)
    init_sentry(settings.SENTRY_DSN_BACKEND, settings.ENV)

    app = FastAPI(
        title="Flow4Food API",
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.ENV != "prod" else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(admin_routes.router, prefix="/api/admin", tags=["admin"])
    app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])
    app.include_router(users_routes.router, prefix="/api/users", tags=["users"])
    app.include_router(profiles_routes.router, prefix="/api/profiles", tags=["profiles"])
    app.include_router(backup_routes.router, prefix="/api/backup", tags=["backup"])
    app.include_router(categorias_routes.router, prefix="/api/categorias", tags=["categorias"])
    app.include_router(config_routes.router, prefix="/api/config", tags=["config"])
    app.include_router(fornecedores_routes.router, prefix="/api/fornecedores", tags=["fornecedores"])
    app.include_router(garcons_routes.router, prefix="/api/garcons", tags=["garcons"])
    app.include_router(metodos_pagamento_routes.router, prefix="/api/metodos-pagamento", tags=["metodos_pagamento"])
    app.include_router(insumos_routes.router, prefix="/api/insumos", tags=["insumos"])
    app.include_router(itens_routes.router, prefix="/api/itens", tags=["itens"])
    app.include_router(produtos_routes.router, prefix="/api/produtos", tags=["produtos"])
    app.include_router(compras_routes.router, prefix="/api/compras", tags=["compras"])
    app.include_router(estoque_routes.router, prefix="/api/estoque", tags=["estoque"])
    app.include_router(relatorios_routes.router, prefix="/api/relatorios", tags=["relatorios"])
    app.include_router(dashboard_routes.router, prefix="/api/dashboard", tags=["dashboard"])
    app.include_router(comandas_routes.router, prefix="/api/comandas", tags=["comandas"])
    app.include_router(contas_pagar_routes.router, prefix="/api/contas-pagar", tags=["contas_pagar"])
    app.include_router(caixa_routes.router, prefix="/api/caixa", tags=["caixa"])

    log = get_logger(__name__)
    log.info("app_started", env=settings.ENV, version=settings.APP_VERSION)

    return app


app = create_app()
