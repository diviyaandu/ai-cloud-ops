"""
agents/finops.py

FinOps Agent — analyses Azure cloud costs and resource inventory.
Currently uses mocked data. When Azure credentials are ready:
  - Set USE_REAL_AZURE = True in tools/azure_cost.py
  - Set USE_REAL_AZURE = True in tools/azure_resource_graph.py
  - No changes needed here.
"""

import asyncio
import json
import os
from typing import Any

from groq import Groq
from mcp_server.client import mcp_call
from agents.actions import propose_action
from agents.tool_selector import select_tools
import state.store as store

ALLOWED_TOOLS = [
    "get_monthly_spend", "get_daily_spend", "get_cost_by_resource_group",
    "get_budget_status", "get_cost_anomalies", "get_full_cost_report",
    "get_advisor_cost_recommendations", "get_untagged_resources",
    "get_full_resource_report",
]

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
_client: Groq | None = None


def _groq() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


SYSTEM_PROMPT = """You are an expert FinOps engineer specialising in Azure cloud cost optimisation and resource governance.
You have been given a full cost report AND a resource inventory report for an Azure subscription.
Answer the user's question based on the data provided.

Guidelines:
- Lead with the most actionable finding (overspend, anomaly, unhealthy resource, or untagged resource)
- Always reference specific dollar amounts from the cost data where relevant
- Cross-reference cost data with resource data when useful (e.g. costly resource groups with unhealthy resources)
- Highlight untagged or ungoverned resources as a cost-visibility risk
- Suggest concrete cost-saving or governance actions where relevant
- Note if data is from a mock/demo environment
- Be concise — 4 paragraphs maximum
- Format currency as $X,XXX.XX
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

    # Auto-propose tagging for untagged resources if fetched
    proposed_actions = []
    untagged = tool_data.get("get_untagged_resources", {}) or \
               tool_data.get("get_full_resource_report", {}).get("untagged_resources", {})
    for r in (untagged.get("resources", []) or [])[:3]:
        rid = r.get("id") or r.get("resource_id")
        if rid:
            proposed_actions.append(propose_action(
                "apply_tags",
                {"resource_id": rid, "tags": {"managed-by": "ai-ops", "auto-tagged": "true"}},
                proposed_by="finops-agent",
            ))

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
            model=GROQ_MODEL, messages=messages, temperature=0.3, max_tokens=512,
        )
        store.increment_groq_calls()
        return response.choices[0].message.content

    answer = await loop.run_in_executor(None, _call)

    return {
        "agent": "finops",
        "agent_label": "💰 FinOps Agent",
        "answer": answer,
        "tool_data": tool_data,
        "overall_status": "ok",
        "proposed_actions": proposed_actions,
    }


# ── Token trimming helpers ─────────────────────────────────────────────────────
# Keep prompts lean for Groq's 6000 TPM free-tier limit.

def _trim_cost_report(report: dict) -> str:
    """Extract the key cost signals rather than dumping the full report."""
    trimmed = {}

    monthly = report.get("monthly_spend", {})
    if monthly and not monthly.get("error"):
        trimmed["monthly_total_usd"] = monthly.get("total")
        trimmed["top_3_services"] = monthly.get("by_service", [])[:3]

    budget = report.get("budget_status", {})
    if budget and not budget.get("error"):
        trimmed["budget"] = {
            "budget_usd":      budget.get("budget_usd"),
            "spent_usd":       budget.get("spent_usd"),
            "percent_used":    budget.get("percent_used"),
            "on_track":        budget.get("on_track"),
            "forecast_eom":    budget.get("forecast_month_end"),
            "status":          budget.get("status"),
        }

    anomalies = report.get("anomalies", {})
    if anomalies and not anomalies.get("error"):
        trimmed["cost_anomalies"] = {
            "count":               len(anomalies.get("anomalies", [])),
            "total_anomaly_cost":  anomalies.get("total_anomaly_cost"),
            "status":              anomalies.get("status"),
            "top_anomaly":         anomalies.get("anomalies", [None])[0],
        }

    by_rg = report.get("by_resource_group", {})
    if by_rg and not by_rg.get("error"):
        trimmed["top_2_resource_groups_by_spend"] = by_rg.get("by_resource_group", [])[:2]

    trimmed["mode"] = report.get("mode", "unknown")
    return json.dumps(trimmed, indent=2)


def _trim_resource_report(report: dict) -> str:
    """Extract the key resource signals rather than dumping the full report."""
    trimmed = {}

    inventory = report.get("inventory", {})
    if inventory and not inventory.get("error"):
        trimmed["total_resources"] = inventory.get("total_resources")
        trimmed["top_3_resource_types"] = inventory.get("by_type", [])[:3]

    unhealthy = report.get("unhealthy_resources", {})
    if unhealthy and not unhealthy.get("error"):
        trimmed["unhealthy"] = {
            "total":    unhealthy.get("total_unhealthy"),
            "critical": unhealthy.get("critical"),
            "warning":  unhealthy.get("warning"),
            "status":   unhealthy.get("status"),
            "resources": unhealthy.get("resources", []),
        }

    untagged = report.get("untagged_resources", {})
    if untagged and not untagged.get("error"):
        trimmed["untagged"] = {
            "total":         untagged.get("total_untagged"),
            "required_tags": untagged.get("required_tags"),
            "status":        untagged.get("status"),
            "examples":      untagged.get("resources", [])[:3],
        }

    recent = report.get("recently_modified_24h", {})
    if recent and not recent.get("error"):
        trimmed["recent_changes_24h"] = {
            "total":   recent.get("total_changes"),
            "changes": recent.get("resources", [])[:3],
        }

    trimmed["mode"] = report.get("mode", "unknown")
    return json.dumps(trimmed, indent=2)