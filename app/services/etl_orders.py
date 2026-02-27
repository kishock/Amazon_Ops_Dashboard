from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.crud import upsert_order
from app.services.slack_notifier import send_sandbox_order_received
from app.services.spapi_client import SPAPIClient


def _build_demo_order_payload() -> dict[str, str]:
    now = datetime.now(timezone.utc)
    iso_ts = now.isoformat().replace("+00:00", "Z")
    return {
        "AmazonOrderId": f"DEMO-{now.strftime('%Y%m%d%H%M%S%f')}",
        "OrderStatus": "Pending",
        "PurchaseDate": iso_ts,
        "LastUpdateDate": iso_ts,
        "OrderType": "DemoSynthetic",
    }


def run_orders_etl(db: Session) -> dict[str, int]:
    client = SPAPIClient()
    orders = client.get_sandbox_orders()
    demo_generated = 0
    slack_events: list[tuple[str, str | None]] = []

    upserted = 0
    try:
        for order in orders:
            _, created = upsert_order(db, order)
            upserted += 1
            if created:
                slack_events.append((order["AmazonOrderId"], order.get("OrderStatus")))

        if settings.demo_mode:
            demo_order = _build_demo_order_payload()
            _, demo_created = upsert_order(db, demo_order)
            upserted += 1
            demo_generated = 1
            if demo_created:
                slack_events.append(
                    (demo_order["AmazonOrderId"], demo_order.get("OrderStatus"))
                )

        db.commit()
    except Exception:
        db.rollback()
        raise

    for order_id, order_status in slack_events:
        send_sandbox_order_received(order_id, order_status)

    return {"fetched": len(orders), "upserted": upserted, "demo_generated": demo_generated}
