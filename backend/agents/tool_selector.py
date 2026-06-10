"""
agents/tool_selector.py
LLM-driven tool selection — picks the right tools for a user query.
"""
import json
import logging
import os
from groq import Groq
import state.store as store

logger = logging.getLogger(__name__)

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

TOOL_DESCRIPTIONS = {
    "get_resource_inventory":               "List all Azure resources by type and region",
    "get_unhealthy_resources":              "Find resources in Failed/Degraded state",
    "get_resource_group_summary":           "Summary of resources per resource group",
    "get_recently_modified_resources":      "Resources changed in last 24h and who changed them",
    "get_untagged_resources":               "Resources missing required tags (governance)",
    "get_full_resource_report":             "Full resource report: inventory + unhealthy + untagged + recent changes",
    "get_recent_errors":                    "Application errors and exceptions in last 24h",
    "get_recent_warnings":                  "Warning-level events in last 24h",
    "get_resource_health_logs":             "Azure Activity Log health and availability events",
    "get_top_operations":                   "Most frequent Azure operations in last 24h",
    "get_failed_operations":                "Failed Azure resource operations in last 24h",
    "get_log_summary":                      "Composite log summary: errors + warnings + health + failed ops",
    "get_monthly_spend":                    "Total Azure spend this month by service",
    "get_daily_spend":                      "Daily spend trend for the last 30 days",
    "get_cost_by_resource_group":           "Spend breakdown by resource group",
    "get_budget_status":                    "Budget utilisation and forecast",
    "get_cost_anomalies":                   "Unusual cost spikes or drops",
    "get_full_cost_report":                 "Full cost report: monthly + budget + anomalies + by RG",
    "get_advisor_cost_recommendations":     "Azure Advisor cost-saving recommendations",
    "get_advisor_security_recommendations": "Azure Advisor security recommendations",
    "get_advisor_reliability_recommendations": "Azure Advisor reliability recommendations",
    "get_advisor_summary":                  "All Azure Advisor recommendations summarised",
}

SYSTEM_PROMPT = f"""You are a tool selector for a cloud operations AI.
Given a user question, pick the 1-4 most relevant tools to call.
Prefer specific tools over composite ones unless the question is broad.
Only use composite tools (get_full_*) when the question is genuinely broad.

Available tools:
{json.dumps(TOOL_DESCRIPTIONS, indent=2)}

Respond with ONLY a JSON array of tool names, e.g.: ["get_unhealthy_resources", "get_log_summary"]
No explanation, no markdown fences.
"""


async def select_tools(user_message: str, allowed: list[str] | None = None) -> list[str]:
    """
    Returns a list of tool names to call for this query.
    `allowed` optionally restricts to a subset of tools.
    """
    import asyncio

    descriptions = TOOL_DESCRIPTIONS
    if allowed:
        descriptions = {k: v for k, v in TOOL_DESCRIPTIONS.items() if k in allowed}

    prompt = f"""Available tools:
{json.dumps(descriptions, indent=2)}

User question: {user_message}

Respond with ONLY a JSON array of tool names."""

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    loop = asyncio.get_event_loop()

    def _call():
        r = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=128,
        )
        store.increment_groq_calls()
        return r.choices[0].message.content

    raw = await loop.run_in_executor(None, _call)
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        tools = json.loads(raw)
        valid = set(TOOL_DESCRIPTIONS.keys())
        tools = [t for t in tools if t in valid]
        logger.info(f"[tool_selector] selected: {tools}")
        return tools
    except Exception:
        return allowed[:2] if allowed else ["get_full_resource_report"]