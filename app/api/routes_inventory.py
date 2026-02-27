"""
Router handling inventory-related API endpoints.
Currently returns an empty list stub.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_inventory() -> dict[str, list]:
    return {"inventory": []}
