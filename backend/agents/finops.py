"""
agents/finops.py

FinOps Agent — analyses Azure cloud costs and resource inventory.
Currently uses mocked data. When Azure credentials are ready:
  - Set USE_REAL_AZURE = True in tools/azure_cost.py
  - Set USE_REAL_AZURE = True in tools/azure_resource_graph.py
  - No changes needed here.
"""

import json
import os
from typing import Any

from groq import Groq
from mcp_server.client import mcp_call

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
    """
    Fetch cost + resource graph data and generate a FinOps-focused response.

    Returns:
        {
            "agent": "finops",
            "answer": str,
            "cost_report": dict,
            "resource_report": dict,
            "overall_status": str,
        }
    """
    import asyncio

    # 1. Fetch cost data and resource graph data in parallel
    cost_report_result, resource_report_result = await asyncio.gather(
        mcp_call("get_full_cost_report"),
        mcp_call("get_full_resource_report"),
        return_exceptions=True,
    )

    cost_report = cost_report_result if not isinstance(cost_report_result, Exception) \
        else {"error": str(cost_report_result), "mode": "error"}

    resource_report = resource_report_result if not isinstance(resource_report_result, Exception) \
        else {"error": str(resource_report_result), "mode": "error"}

    # Derive overall status from budget, cost anomalies, and unhealthy resources
    budget    = cost_report.get("budget_status", {})
    anomalies = cost_report.get("anomalies", {})
    unhealthy = resource_report.get("unhealthy_resources", {})
    untagged  = resource_report.get("untagged_resources", {})

    statuses = [
        budget.get("status", "ok"),
        anomalies.get("status", "ok"),
        unhealthy.get("status", "ok"),
        untagged.get("status", "ok"),
    ]
    if "critical" in statuses:
        overall_status = "critical"
    elif "warning" in statuses:
        overall_status = "warning"
    else:
        overall_status = "ok"

    # 2. Build a trimmed summary to stay within Groq token limits
    #    Send key signals rather than raw full dumps
    cost_summary = _trim_cost_report(cost_report)
    resource_summary = _trim_resource_report(resource_report)

    cost_mode    = cost_report.get("mode", "unknown")
    resource_mode = resource_report.get("mode", "unknown")
    mode_note = ""
    if cost_mode == "mock" or resource_mode == "mock":
        mode_note = "(NOTE: data is MOCK — set USE_REAL_AZURE=True in tools/azure_cost.py and tools/azure_resource_graph.py for live data)"

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        messages.extend(history[-6:])

    messages.append({
        "role": "user",
        "content": (
            f"AZURE COST REPORT {mode_note}:\n```json\n{cost_summary}\n```\n\n"
            f"AZURE RESOURCE REPORT:\n```json\n{resource_summary}\n```\n\n"
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
        "agent": "finops",
        "agent_label": "💰 FinOps Agent",
        "answer": answer,
        "cost_report": cost_report,
        "resource_report": resource_report,
        "overall_status": overall_status,
        "data_mode": cost_mode,
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