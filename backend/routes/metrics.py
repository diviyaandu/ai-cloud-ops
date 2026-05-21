from fastapi import APIRouter
from services.metrics import get_system_metrics

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def metrics():
    """Pure metric collection — zero Groq calls. Poll freely."""
    return await get_system_metrics()