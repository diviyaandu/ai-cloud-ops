"""
routes/cloud_summary.py

GET /cloud-summary
Single endpoint that aggregates all insight data for the Overview dashboard.
Runs all fetches in parallel — one HTTP call from frontend instead of four.
"""
import asyncio
from fastapi import APIRouter
from tools.azure_resource_graph import (
    get_resource_inventory,
    get_unhealthy_resources,
    get_untagged_resources,
    get_recently_modified_resources,
)
from tools.azure_cost import get_budget_status
from tools.azure_log_analytics import get_recent_errors, get_failed_operations
from tools.azure_advisor import get_advisor_cost_recommendations

router = APIRouter()


@router.get("/cloud-summary")
async def cloud_summary():
    results = await asyncio.gather(
        get_unhealthy_resources(),
        get_untagged_resources(),
        get_recently_modified_resources(24),
        get_budget_status(),
        get_recent_errors(),
        get_failed_operations(),
        get_advisor_cost_recommendations(),
        return_exceptions=True,
    )

    def _safe(r, fallback=None):
        return r if not isinstance(r, Exception) else (fallback or {"error": str(r)})

    unhealthy  = _safe(results[0], {})
    untagged   = _safe(results[1], {})
    recent     = _safe(results[2], {})
    budget     = _safe(results[3], {})
    errors     = _safe(results[4], {})
    failed_ops = _safe(results[5], {})
    advisor    = _safe(results[6], {})

    return {
        "spend": {
            "spent_usd":        budget.get("spent_usd"),
            "budget_usd":       budget.get("budget_usd"),
            "forecast_eom_usd": budget.get("forecast_month_end"),
            "percent_used":     budget.get("percent_used"),
            "status":           budget.get("status", "unknown"),
        },
        "health": {
            "unhealthy_total":  unhealthy.get("total_unhealthy", 0),
            "critical":         unhealthy.get("critical", 0),
            "warning":          unhealthy.get("warning", 0),
            "status":           unhealthy.get("status", "ok"),
            "resources":        unhealthy.get("resources", [])[:3],
        },
        "security": {
            "untagged_total":   untagged.get("total_untagged", 0),
            "recent_changes":   recent.get("total_changes", 0),
            "status":           "warning" if untagged.get("total_untagged", 0) > 0 else "ok",
        },
        "logs": {
            "errors_24h":       errors.get("total", 0),
            "failed_ops_24h":   failed_ops.get("total", 0),
            "status":           errors.get("status", "ok"),
        },
        "advisor": {
            "total":            advisor.get("total", 0),
            "potential_savings": advisor.get("total_potential_savings_usd", 0),
            "status":           advisor.get("status", "ok"),
        },
    }
