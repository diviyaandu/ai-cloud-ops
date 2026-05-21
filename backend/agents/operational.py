"""
agents/operational.py

Operational Agent — answers questions about system health using real Prometheus data.
Fetches live metrics, then asks Groq to interpret them in context of the user's question.
"""

import json
import os
from typing import Any

from groq import Groq
from tools.registry import get_all_metrics

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
_client: Groq | None = None


def _groq() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


SYSTEM_PROMPT = """You are an expert Site Reliability Engineer (SRE) AI assistant.
You have been given live system metrics from Prometheus. Answer the user's question
concisely and precisely. Focus on actionable insights. If something looks wrong, say
what it is and what to do about it. Use plain language — no jargon unless the user
clearly knows what they're doing.

Metric status levels: ok = healthy, warning = investigate, critical = act now.

Format your response in 2–3 short paragraphs maximum. Lead with the most important finding.
"""


async def run(user_message: str, history: list[dict] | None = None) -> dict[str, Any]:
    """
    Fetch live metrics and generate an SRE-focused response.

    Returns:
        {
            "agent": "operational",
            "answer": str,
            "metrics_snapshot": dict,
            "overall_status": str,
        }
    """
    import asyncio

    # 1. Fetch live Prometheus data
    try:
        metrics = await get_all_metrics()
    except Exception as e:
        metrics = {"error": str(e), "overall_status": "unknown"}

    overall_status = metrics.get("overall_status", "unknown")

    # 2. Build the prompt
    metrics_summary = json.dumps(metrics, indent=2)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Include recent conversation history (last 6 turns)
    if history:
        messages.extend(history[-6:])

    messages.append({
        "role": "user",
        "content": (
            f"LIVE METRICS (from Prometheus):\n```json\n{metrics_summary}\n```\n\n"
            f"USER QUESTION: {user_message}"
        ),
    })

    # 3. Call Groq
    loop = asyncio.get_event_loop()

    def _call():
        response = _groq().chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=512,
        )
        return response.choices[0].message.content

    answer = await loop.run_in_executor(None, _call)

    return {
        "agent": "operational",
        "agent_label": "⚙️ Operational Agent",
        "answer": answer,
        "metrics_snapshot": metrics,
        "overall_status": overall_status,
    }