"""
Router for order management endpoints.
Currently a placeholder returning an empty order list.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_orders() -> dict[str, list]:
    return {"orders": []}
