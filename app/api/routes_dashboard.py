"""
Router for dashboard-related endpoints.
Includes a simple health check used for service monitoring.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
