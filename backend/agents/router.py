"""
agents/router.py

Routing Agent — classifies user intent and dispatches to the correct sub-agent.
Runs as the entry node in the LangGraph graph.

Intent classes:
  - "operational"  → Azure resource health, inventory, logs, errors, uptime
  - "security"     → governance, untagged resources, recent changes, audit,
                     access control, vulnerabilities, who changed what
  - "finops"       → Azure costs, budgets, spend, billing, cost anomalies
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
                 uptime, performance, node health, errors, failed operations,
                 Azure logs, application errors, warnings, activity log,
                 "what's the health of my infrastructure", "what's running",
                 "are my services healthy", "what resources are currently running",
                 "what's deployed", "show me my resources", "list my resources",
                 "are there any errors in my logs", "any failed operations",
                 "what do I have running", "what resources do I have"

  security     — questions about governance, compliance, resource hygiene,
                 untagged resources, missing tags, recently modified resources,
                 who changed what, change history, suspicious changes,
                 access control, RBAC, login attempts, open ports,
                 security audit, vulnerabilities, exposed resources,
                 "are there untagged resources", "what changed recently",
                 "who modified my resources", "any governance issues",
                 "are my resources compliant", "run a security audit",
                 "any security risks", "what resources are ungoverned"

  finops       — questions about Azure costs, spend, budgets, billing,
                 cost anomalies, cost by resource group, forecasts,
                 "how much am I spending", "what's my Azure bill",
                 "show me costs", "am I over budget", "cost breakdown"

  general      — greetings, off-topic, or anything that doesn't fit above

Key rules:
  - resource health / status / errors / logs → operational
  - cost / spend / billing / budget / forecast → finops
  - untagged / governance / who changed / compliance / audit / RBAC → security
  - When in doubt between operational and security, check: does it involve
    WHO did something or compliance? → security. Does it involve WHAT is
    running or broken? → operational

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