"""
agents/operational.py

Operational Agent — answers questions about Azure resource health and inventory.
Pulls live data from Azure Resource Graph via the MCP server.
"""

import json
import os
from typing import Any

from groq import Groq
from mcp_server.client import mcp_call
import state.store as store

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
_client: Groq | None = None


def _groq() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


SYSTEM_PROMPT = """You are an expert Azure cloud operations engineer.
You have been given live data from Azure Resource Graph about the user's subscription.
Answer the user's question concisely and precisely based on this data.

Guidelines:
- Lead with the most important finding (unhealthy resources, recent changes, or inventory summary)
- Reference specific resource names, types, and regions where relevant
- If resources are unhealthy or recently modified, highlight them
- Suggest concrete next steps where relevant
- Be concise — 3 paragraphs maximum
- Status levels: ok = healthy, warning = investigate, critical = act now
"""


async def run(user_message: str, history: list[dict] | None = None) -> dict[str, Any]:
    import asyncio

    # Fetch inventory + unhealthy resources in parallel
    inventory_result, unhealthy_result, logs_result = await asyncio.gather(
        mcp_call("get_resource_inventory"),
        mcp_call("get_unhealthy_resources"),
        mcp_call("get_log_summary"),
        return_exceptions=True,
    )

    inventory = inventory_result if not isinstance(inventory_result, Exception) \
        else {"error": str(inventory_result)}
    unhealthy = unhealthy_result if not isinstance(unhealthy_result, Exception) \
        else {"error": str(unhealthy_result)}
    logs = logs_result if not isinstance(logs_result, Exception) \
        else {"error": str(logs_result)}

    # Derive status
    overall_status = unhealthy.get("status", "ok") if not unhealthy.get("error") else "unknown"

    # Trim to stay within token limits
    summary = {
        "total_resources": inventory.get("total_resources", 0),
        "by_type": inventory.get("by_type", [])[:10],
        "mode": inventory.get("mode", "unknown"),
        "unhealthy": {
            "total": unhealthy.get("total_unhealthy", 0),
            "critical": unhealthy.get("critical", 0),
            "warning": unhealthy.get("warning", 0),
            "status": unhealthy.get("status", "ok"),
            "resources": unhealthy.get("resources", [])[:5],
        },
        "logs": {
            "errors_24h":   logs.get("recent_errors", {}).get("total", 0),
            "warnings_24h": logs.get("recent_warnings", {}).get("total", 0),
            "failed_ops":   logs.get("failed_operations", {}).get("total", 0),
            "health_events": logs.get("resource_health", {}).get("total", 0),
            "overall":      logs.get("overall_status", "unknown"),
        },
    }

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-6:])
    messages.append({
        "role": "user",
        "content": (
            f"AZURE RESOURCE DATA (live):\n```json\n{json.dumps(summary, indent=2)}\n```\n\n"
            f"USER QUESTION: {user_message}"
        ),
    })

    loop = asyncio.get_event_loop()

    def _call():
        response = _groq().chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=512,
        )
        store.increment_groq_calls()
        return response.choices[0].message.content

    answer = await loop.run_in_executor(None, _call)

    return {
        "agent": "operational",
        "agent_label": "⚙️ Operational Agent",
        "answer": answer,
        "inventory": inventory,
        "unhealthy": unhealthy,
        "overall_status": overall_status,
    }
