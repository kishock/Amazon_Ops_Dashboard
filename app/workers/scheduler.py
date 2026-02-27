"""
Starts background scheduler for periodic tasks.
Currently a stub returning a simple status dictionary.
"""

from app.db.session import SessionLocal
from app.services.etl_orders import run_orders_etl


def run_orders_sync_once() -> dict[str, int]:
    db = SessionLocal()
    try:
        return run_orders_etl(db)
    finally:
        db.close()
