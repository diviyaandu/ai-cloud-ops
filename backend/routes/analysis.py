from fastapi import APIRouter
from services.analysis import get_analysis

router = APIRouter(tags=["analysis"])


@router.get("/analyze")
async def analyze(force: bool = False):
    """
    Returns AI analysis of current metrics.
    Groq is called only when force=true, or cooldown elapsed AND metrics shifted.
    """
    return await get_analysis(force=force)