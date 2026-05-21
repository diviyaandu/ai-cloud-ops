"""
agents/router.py

Routing Agent — classifies user intent and dispatches to the correct sub-agent.
Runs as the entry node in the LangGraph graph.

Intent classes:
  - "operational"  → CPU, memory, disk, HTTP errors, Prometheus metrics
  - "security"     → ports, SSH failures, suspicious processes, audit
  - "finops"       → Azure costs, budgets, spend anomalies
  - "general"      → catch-all, answered directly without a sub-agent
"""

import json
import os
from typing import Literal

from groq import Groq

AgentType = Literal["operational", "security", "finops", "general"]

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
_client: Groq | None = None


def _groq() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


SYSTEM_PROMPT = """You are a routing agent for a cloud operations AI system.
Your ONLY job is to classify the user's message into exactly one of these categories:

  operational  — questions about system metrics, CPU, memory, disk, network,
                 HTTP errors, Prometheus data, uptime, performance
  security     — questions about open ports, SSH failures, suspicious processes,
                 security audits, vulnerabilities, access control
  finops       — questions about Azure costs, spend, budgets, billing,
                 resource costs, cost anomalies, FinOps
  general      — greetings, off-topic, or anything that doesn't fit above

Respond with ONLY a JSON object, no explanation:
{"intent": "<category>", "confidence": <0.0-1.0>, "reasoning": "<one sentence>"}
"""


async def classify_intent(user_message: str) -> dict:
    """
    Returns:
        {
            "intent": "operational" | "security" | "finops" | "general",
            "confidence": float,
            "reasoning": str,
        }
    """
    import asyncio

    loop = asyncio.get_event_loop()

    def _call():
        response = _groq().chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            max_tokens=128,
        )
        return response.choices[0].message.content

    raw = await loop.run_in_executor(None, _call)

    # Strip markdown fences if model wraps in ```json
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: default to operational if we can't parse
        parsed = {"intent": "operational", "confidence": 0.5, "reasoning": "parse error — defaulting"}

    # Validate intent value
    valid = {"operational", "security", "finops", "general"}
    if parsed.get("intent") not in valid:
        parsed["intent"] = "general"

    return parsed