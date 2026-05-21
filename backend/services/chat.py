from models.schemas import ChatRequest
from services.metrics import get_system_metrics, build_metrics_summary
from services.groq_client import call_groq
import state.store as store

_SYSTEM_TEMPLATE = """\
You are a senior Site Reliability Engineer assistant.
Live system snapshot:
{summary}

Rules:
- Reference actual metric values
- Max 3 bullet points or 4 sentences
- Be direct and actionable
- No generic AI disclaimers\
"""

MAX_HISTORY = 10


async def handle_chat(request: ChatRequest) -> dict:
    """Build context-aware prompt and call Groq. 1 call per user message."""
    data    = await get_system_metrics()
    summary = build_metrics_summary(data)

    system_prompt = _SYSTEM_TEMPLATE.format(summary=summary)

    history_messages = [
        {
            "role":    "assistant" if msg.role == "assistant" else "user",
            "content": msg.text,
        }
        for msg in request.history[-MAX_HISTORY:]
    ]
    history_messages.append({"role": "user", "content": request.message})

    response = call_groq(
        system=system_prompt,
        messages=history_messages,
        max_tokens=300,
        temperature=0.4,
    )

    return {
        "response":         response,
        "groq_calls_total": store.groq_call_count,
    }