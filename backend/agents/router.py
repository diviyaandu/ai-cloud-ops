"""
agents/router.py

Routing Agent — classifies user intent and dispatches to the correct sub-agent.
Runs as the entry node in the LangGraph graph.

Intent classes:
  - "operational"  → CPU, memory, disk, HTTP errors, Prometheus metrics
  - "security"     → ports, SSH failures, suspicious processes, audit
  - "finops"       → Azure costs, budgets, spend, billing, resource inventory,
                     unhealthy resources, untagged resources, resource graph
  - "general"      → catch-all, answered directly without a sub-agent
"""

import json
import os
from typing import Literal

from groq import Groq
import state.store as store

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

  operational  — questions about cloud resource health, infrastructure state,
                 what is running, resource status, VM state, service health,
                 uptime, performance, node health, is something up/down,
                 "what's the health of my infrastructure", "what's running",
                 "are my services healthy", "what resources are currently running",
                 "what's deployed", "show me my resources", "list my resources",
                 "what do I have running", "what resources do I have"

  security     — questions about open ports, SSH failures, suspicious processes,
                 security audits, vulnerabilities, access control, login attempts

  finops       — questions about Azure costs, spend, budgets, billing,
                 cost anomalies, untagged resources, cost by resource group,
                 "how much am I spending", "what's my Azure bill", "show me costs"

  general      — greetings, off-topic, or anything that doesn't fit above

Key rules:
  - resource health / status / running state → operational
  - cost / spend / billing / budget → finops
  - security / ports / SSH / audit → security
  - When in doubt between operational and finops, prefer operational

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
        store.increment_groq_calls()
        return response.choices[0].message.content

    raw = await loop.run_in_executor(None, _call)

    # Strip markdown fences if model wraps in ```json
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"intent": "general", "confidence": 0.5, "reasoning": "parse error — defaulting"}

    # Validate intent value
    valid = {"operational", "security", "finops", "general"}
    if parsed.get("intent") not in valid:
        parsed["intent"] = "general"

    return parsed