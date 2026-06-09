"""
tools/registry.py

Central tool registry — the MCP tool bus.
Each agent imports from here rather than directly from tool modules.
Keeps the tool surface explicit and testable.
"""

from tools.azure_cost import (
    get_monthly_spend,
    get_daily_spend,
    get_cost_by_resource_group,
    get_budget_status,
    get_cost_anomalies,
    get_full_cost_report,
)

from tools.azure_resource_graph import (
    get_resource_inventory,
    get_unhealthy_resources,
    get_resource_group_summary,
    get_recently_modified_resources,
    get_untagged_resources,
    get_full_resource_report,
)

from tools.azure_log_analytics import (
    get_recent_errors,
    get_recent_warnings,
    get_resource_health_logs,
    get_top_operations,
    get_failed_operations,
    get_log_summary,
)
from tools.azure_advisor import (
    get_advisor_recommendations,
    get_advisor_cost_recommendations,
    get_advisor_security_recommendations,
    get_advisor_reliability_recommendations,
    get_advisor_summary,
)

TOOL_REGISTRY: dict = {
    # FinOps — Cost Management
    "get_monthly_spend":            get_monthly_spend,
    "get_daily_spend":              get_daily_spend,
    "get_cost_by_resource_group":   get_cost_by_resource_group,
    "get_budget_status":            get_budget_status,
    "get_cost_anomalies":           get_cost_anomalies,
    "get_full_cost_report":         get_full_cost_report,
    # Azure Resource Graph
    "get_resource_inventory":           get_resource_inventory,
    "get_unhealthy_resources":          get_unhealthy_resources,
    "get_resource_group_summary":       get_resource_group_summary,
    "get_recently_modified_resources":  get_recently_modified_resources,
    "get_untagged_resources":           get_untagged_resources,
    "get_full_resource_report":         get_full_resource_report,
    "get_recent_errors":        get_recent_errors,
    "get_recent_warnings":      get_recent_warnings,
    "get_resource_health_logs": get_resource_health_logs,
    "get_top_operations":       get_top_operations,
    "get_failed_operations":    get_failed_operations,
    "get_log_summary":          get_log_summary,
    "get_advisor_recommendations":          get_advisor_recommendations,
    "get_advisor_cost_recommendations":     get_advisor_cost_recommendations,
    "get_advisor_security_recommendations": get_advisor_security_recommendations,
    "get_advisor_reliability_recommendations": get_advisor_reliability_recommendations,
    "get_advisor_summary":                  get_advisor_summary,
}


async def call_tool(name: str, **kwargs) -> dict:
    """Call a registered tool by name. Raises KeyError if not found."""
    if name not in TOOL_REGISTRY:
        raise KeyError(f"Unknown tool: {name!r}. Available: {list(TOOL_REGISTRY)}")
    return await TOOL_REGISTRY[name](**kwargs)