"""
agents/security.py

Security Agent — audits Azure resources for security posture.
Uses Azure Resource Graph to surface untagged, recently modified,
and potentially ungoverned resources. Local psutil removed.
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
    import asyncio

    # Fetch untagged + recently modified + unhealthy in parallel
    untagged_result, recent_result, unhealthy_result, advisor_result = await asyncio.gather(
        mcp_call("get_untagged_resources"),
        mcp_call("get_recently_modified_resources"),
        mcp_call("get_unhealthy_resources"),
        mcp_call("get_advisor_security_recommendations"),
        return_exceptions=True,
    )
    advisor = advisor_result if not isinstance(advisor_result, Exception) else {"error": str(advisor_result)}
    untagged  = untagged_result  if not isinstance(untagged_result,  Exception) else {"error": str(untagged_result)}
    recent    = recent_result    if not isinstance(recent_result,    Exception) else {"error": str(recent_result)}
    unhealthy = unhealthy_result if not isinstance(unhealthy_result, Exception) else {"error": str(unhealthy_result)}

    # Derive overall status
    statuses = [
        untagged.get("status", "ok"),
        unhealthy.get("status", "ok"),
    ]
    if "critical" in statuses:
        overall_status = "critical"
    elif "warning" in statuses:
        overall_status = "warning"
    else:
        overall_status = "ok"

    summary = {
        "untagged_resources": {
            "total": untagged.get("total_untagged", 0),
            "required_tags": untagged.get("required_tags", []),
            "status": untagged.get("status", "ok"),
            "examples": untagged.get("resources", [])[:5],
        },
        "recently_modified": {
            "total": recent.get("total_changes", 0),
            "window": recent.get("window", "24h"),
            "changes": recent.get("resources", [])[:5],
        },
        "unhealthy_resources": {
            "total": unhealthy.get("total_unhealthy", 0),
            "critical": unhealthy.get("critical", 0),
            "warning": unhealthy.get("warning", 0),
            "status": unhealthy.get("status", "ok"),
            "resources": unhealthy.get("resources", [])[:5],
        },
        "advisor_security": {
            "total": advisor.get("total", 0),
            "high":  advisor.get("high", 0),
            "status": advisor.get("status", "unknown"),
            "top": [r["problem"] + " → " + r["solution"]
                    for r in advisor.get("recommendations", [])[:3]],
        },
    }

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-6:])
    messages.append({
        "role": "user",
        "content": (
            f"AZURE SECURITY DATA (live):\n```json\n{json.dumps(summary, indent=2)}\n```\n\n"
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
        "untagged": untagged,
        "recently_modified": recent,
        "unhealthy": unhealthy,
        "overall_status": overall_status,
    }