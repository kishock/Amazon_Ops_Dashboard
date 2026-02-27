from sqlalchemy.orm import Session

from app.db.crud import upsert_order
from app.services.spapi_client import SPAPIClient


def run_orders_etl(db: Session) -> dict[str, int]:
    client = SPAPIClient()
    orders = client.get_sandbox_orders()

    upserted = 0
    try:
        for order in orders:
            upsert_order(db, order)
            upserted += 1
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"fetched": len(orders), "upserted": upserted}
