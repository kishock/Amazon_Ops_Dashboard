"""
Router exposing log retrieval endpoints.
Stub implementation returns an empty list.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_logs() -> dict[str, list]:
    return {"logs": []}
