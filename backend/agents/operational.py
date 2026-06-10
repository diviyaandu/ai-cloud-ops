"""
agents/operational.py

Operational Agent — answers questions about Azure resource health and inventory.
Pulls live data from Azure Resource Graph via the MCP server.
"""

import json
import os
import asyncio
from typing import Any

from groq import Groq
from agents.tool_selector import select_tools
from mcp_server.client import mcp_call
import state.store as store

ALLOWED_TOOLS = [
    "get_resource_inventory", "get_unhealthy_resources",
    "get_resource_group_summary", "get_log_summary",
    "get_recent_errors", "get_failed_operations",
    "get_resource_health_logs", "get_full_resource_report",
]

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
    # 1. Select tools dynamically
    tools = await select_tools(user_message, allowed=ALLOWED_TOOLS)

    # 2. Call selected tools in parallel
    results = await asyncio.gather(
        *[mcp_call(t) for t in tools], return_exceptions=True
    )
    tool_data = {
        t: (r if not isinstance(r, Exception) else {"error": str(r)})
        for t, r in zip(tools, results)
    }

    overall_status = "ok"
    for v in tool_data.values():
        s = v.get("status", "ok")
        if s == "critical":
            overall_status = "critical"
        elif s == "warning" and overall_status != "critical":
            overall_status = "warning"

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-6:])
    messages.append({
        "role": "user",
        "content": (
            f"AZURE DATA:\n```json\n{json.dumps(tool_data, indent=2)}\n```\n\n"
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
        "tool_data": tool_data,
        "overall_status": overall_status,
    }
