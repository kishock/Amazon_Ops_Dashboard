"""
Application entry point defining FastAPI instance and registering route modules.

Each router module in `app.api` exposes endpoints for different
areas of the Amazon Ops Dashboard (dashboard, orders, inventory, logs).
"""
from fastapi import FastAPI

from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_inventory import router as inventory_router
from app.api.routes_logs import router as logs_router
from app.api.routes_orders import router as orders_router


def create_app() -> FastAPI:
    app = FastAPI(title="Amazon Ops Dashboard API")
    app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
    app.include_router(orders_router, prefix="/orders", tags=["orders"])
    app.include_router(inventory_router, prefix="/inventory", tags=["inventory"])
    app.include_router(logs_router, prefix="/logs", tags=["logs"])
    return app


app = create_app()
