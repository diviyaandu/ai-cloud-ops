"""
agents/security.py

Security Agent — audits Azure resources for security posture.
Uses Azure Resource Graph to surface untagged, recently modified,
and potentially ungoverned resources. Local psutil removed.
"""

import asyncio
import json
import os
from typing import Any

from groq import Groq
from mcp_server.client import mcp_call
from agents.tool_selector import select_tools
import state.store as store

ALLOWED_TOOLS = [
    "get_untagged_resources", "get_recently_modified_resources",
    "get_unhealthy_resources", "get_advisor_security_recommendations",
    "get_advisor_reliability_recommendations", "get_resource_health_logs",
    "get_failed_operations", "get_full_resource_report",
]

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
_client: Groq | None = None


def _groq() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


SYSTEM_PROMPT = """You are an Azure cloud security analyst.
You have been given live data from Azure Resource Graph about the user's subscription.
Your job is to identify security and governance risks based on this data.

Guidelines:
- Lead with the highest-risk finding
- Untagged resources = governance risk (no owner, no cost centre, harder to audit)
- Recently modified resources = change risk (who changed what, and why)
- Unhealthy resources = availability and security risk
- Use CRITICAL / WARNING / OK labels
- Suggest concrete remediation steps
- Be concise — 3 paragraphs maximum
- Note: Azure Security Center / Defender integration is a recommended next step for deeper posture data
"""


async def run(user_message: str, history: list[dict] | None = None) -> dict[str, Any]:
    tools = await select_tools(user_message, allowed=ALLOWED_TOOLS)

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
            f"AZURE SECURITY DATA (live):\n```json\n{json.dumps(tool_data, indent=2)}\n```\n\n"
            f"USER QUESTION: {user_message}"
        ),
    })

    loop = asyncio.get_event_loop()

    def _call():
        response = _groq().chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=512,
        )
        store.increment_groq_calls()
        return response.choices[0].message.content

    answer = await loop.run_in_executor(None, _call)

    return {
        "agent": "security",
        "agent_label": "🔒 Security Agent",
        "answer": answer,
        "tool_data": tool_data,
        "overall_status": overall_status,
    }