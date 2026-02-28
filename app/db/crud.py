from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Order


def _parse_spapi_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized).astimezone(timezone.utc)


def upsert_order(db: Session, order_payload: dict) -> tuple[Order, bool]:
    amazon_order_id = order_payload["AmazonOrderId"]
    existing = db.query(Order).filter(Order.amazon_order_id == amazon_order_id).one_or_none()
    created = existing is None

    if existing is None:
        existing = Order(amazon_order_id=amazon_order_id, raw_payload=order_payload)
        db.add(existing)

    existing.order_status = order_payload.get("OrderStatus")
    existing.purchase_date = _parse_spapi_datetime(order_payload.get("PurchaseDate"))
    existing.last_update_date = _parse_spapi_datetime(order_payload.get("LastUpdateDate"))
    existing.raw_payload = order_payload
    existing.synced_at = datetime.utcnow()
    return existing, created


def list_orders(db: Session, limit: int = 100) -> list[Order]:
    return db.query(Order).order_by(Order.id.desc()).limit(limit).all()


def delete_all_orders(db: Session) -> int:
    deleted_count = db.query(Order).delete(synchronize_session=False)
    db.commit()
    return deleted_count
