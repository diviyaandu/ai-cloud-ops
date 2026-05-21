from fastapi import APIRouter
from models.schemas import ChatRequest
from services.chat import handle_chat

router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat(request: ChatRequest):
    """1 Groq call per user message. Live metrics injected as context."""
    return await handle_chat(request)