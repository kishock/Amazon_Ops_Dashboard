import random
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.crud import upsert_order
from app.services.slack_notifier import send_sandbox_order_received
from app.services.spapi_client import SPAPIClient


def _build_order_extensions() -> dict[str, str | float]:
    buyer_names = [
        "Alex Carter",
        "Jordan Lee",
        "Taylor Kim",
        "Morgan Park",
        "Casey Smith",
        "Jamie Chen",
    ]
    amount = round(random.uniform(25, 500), 2)
    cost = round(random.uniform(10, amount * 0.8), 2)
    return {
        "Buyer": random.choice(buyer_names),
        "Amount": amount,
        "Cost": cost,
    }


def _enrich_order_payload(order_payload: dict) -> dict:
    enriched_payload = dict(order_payload)
    enriched_payload.update(_build_order_extensions())
    return enriched_payload


def _serialize_order_summary(order_payload: dict) -> dict[str, str | float | None]:
    return {
        "amazon_order_id": order_payload.get("AmazonOrderId"),
        "order_status": order_payload.get("OrderStatus"),
        "purchase_date": order_payload.get("PurchaseDate"),
        "last_update_date": order_payload.get("LastUpdateDate"),
        "Buyer": order_payload.get("Buyer"),
        "Amount": order_payload.get("Amount"),
        "Cost": order_payload.get("Cost"),
    }


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


def run_orders_etl(db: Session) -> dict[str, int | list[dict[str, str | float | None]]]:
    client = SPAPIClient()
    orders = client.get_sandbox_orders()
    demo_generated = 0
    slack_events: list[tuple[str, str | None]] = []
    synced_orders: list[dict[str, str | float | None]] = []

    upserted = 0
    try:
        for order in orders:
            enriched_order = _enrich_order_payload(order)
            _, created = upsert_order(db, enriched_order)
            upserted += 1
            synced_orders.append(_serialize_order_summary(enriched_order))
            if created:
                slack_events.append(
                    (enriched_order["AmazonOrderId"], enriched_order.get("OrderStatus"))
                )

        if settings.demo_mode:
            demo_order = _enrich_order_payload(_build_demo_order_payload())
            _, demo_created = upsert_order(db, demo_order)
            upserted += 1
            demo_generated = 1
            synced_orders.append(_serialize_order_summary(demo_order))
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

    return {
        "fetched": len(orders),
        "upserted": upserted,
        "demo_generated": demo_generated,
        "orders": synced_orders,
    }
