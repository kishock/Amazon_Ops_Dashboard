import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.crud import list_orders
from app.db.session import get_db
from app.services.etl_orders import run_orders_etl

router = APIRouter()


@router.get("/")
def get_orders(db: Session = Depends(get_db)) -> dict[str, list[dict]]:
    rows = list_orders(db)
    return {
        "orders": [
            {
                "id": row.id,
                "amazon_order_id": row.amazon_order_id,
                "order_status": row.order_status,
                "purchase_date": row.purchase_date.isoformat() if row.purchase_date else None,
                "last_update_date": row.last_update_date.isoformat()
                if row.last_update_date
                else None,
                "synced_at": row.synced_at.isoformat() if row.synced_at else None,
            }
            for row in rows
        ]
    }


@router.post("/sync-sandbox")
def sync_sandbox_orders(db: Session = Depends(get_db)) -> dict[str, int]:
    try:
        return run_orders_etl(db)
    except RuntimeError as exc:
        if "Missing SP-API credentials" in str(exc):
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        raise
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else 502
        raise HTTPException(
            status_code=502,
            detail=f"SP-API request failed with status {status_code}",
        ) from exc
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail=f"SP-API request failed: {exc.__class__.__name__}",
        ) from exc
