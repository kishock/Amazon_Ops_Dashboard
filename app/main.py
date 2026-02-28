from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_inventory import router as inventory_router
from app.api.routes_logs import router as logs_router
from app.api.routes_orders import router as orders_router
from app.core.config import settings
from app.db import models  # noqa: F401
from app.db.session import Base, engine, ensure_orders_extension_columns


def create_app() -> FastAPI:
    app = FastAPI(title="Amazon Ops Dashboard API")

    if settings.cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
    app.include_router(orders_router, prefix="/orders", tags=["orders"])
    app.include_router(inventory_router, prefix="/inventory", tags=["inventory"])
    app.include_router(logs_router, prefix="/logs", tags=["logs"])

    @app.on_event("startup")
    def _startup() -> None:
        Base.metadata.create_all(bind=engine)
        ensure_orders_extension_columns()

    return app


app = create_app()
