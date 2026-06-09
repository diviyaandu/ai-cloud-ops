"""
tools/azure_advisor.py

Azure Advisor toolbox — fetches recommendations from Azure Advisor REST API.

Categories available:
  - Cost         : rightsizing, reserved instances, unused resources
  - Security     : security posture, exposed resources, weak configs
  - Reliability  : high availability, backup, resilience
  - Performance  : throughput, latency improvements
  - Operational  : best practices, monitoring gaps

Requires:
  - Service principal with Reader role (already have this)
  - Env vars: AZURE_SUBSCRIPTION_ID, AZURE_TENANT_ID,
              AZURE_CLIENT_ID, AZURE_CLIENT_SECRET
"""

import os
import asyncio
import requests
from datetime import datetime, timezone
from typing import Any

SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID", "")
ADVISOR_URL = (
    f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}"
    f"/providers/Microsoft.Advisor/recommendations?api-version=2023-01-01"
)

_credential = None


def _get_credential():
    global _credential
    if _credential is None:
        from azure.identity import ClientSecretCredential
        _credential = ClientSecretCredential(
            tenant_id=os.getenv("AZURE_TENANT_ID", ""),
            client_id=os.getenv("AZURE_CLIENT_ID", ""),
            client_secret=os.getenv("AZURE_CLIENT_SECRET", ""),
        )
    return _credential


def _fetch_recommendations() -> list[dict]:
    """Fetch all Advisor recommendations, handling pagination."""
    token = _get_credential().get_token("https://management.azure.com/.default").token
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    results = []
    url = ADVISOR_URL

    while url:
        resp = requests.get(url, headers=headers, timeout=30)
        if not resp.ok:
            raise RuntimeError(
                f"Azure Advisor API failed ({resp.status_code}): {resp.text[:300]}"
            )
        data = resp.json()
        results.extend(data.get("value", []))
        url = data.get("nextLink")  # handle pagination

    return results


def _parse_recommendation(raw: dict) -> dict:
    """Normalize a raw Advisor recommendation into a clean dict."""
    props = raw.get("properties", {})
    impact = props.get("impact", "Low")
    category = props.get("category", "Unknown")

    resource_id = props.get("resourceMetadata", {}).get("resourceId", "")
    resource_name = resource_id.split("/")[-1] if resource_id else "unknown"
    resource_group = ""
    parts = resource_id.lower().split("/")
    if "resourcegroups" in parts:
        idx = parts.index("resourcegroups")
        resource_group = parts[idx + 1] if idx + 1 < len(parts) else ""

    return {
        "id":             raw.get("id", ""),
        "category":       category,
        "impact":         impact,
        "severity":       "critical" if impact == "High" else "warning" if impact == "Medium" else "ok",
        "resource_name":  resource_name,
        "resource_group": resource_group,
        "resource_id":    resource_id,
        "problem":        props.get("shortDescription", {}).get("problem", ""),
        "solution":       props.get("shortDescription", {}).get("solution", ""),
        "potential_savings_usd": (
            props.get("extendedProperties", {}).get("annualSavingsAmount")
        ),
    }


# ── Public tool functions ──────────────────────────────────────────────────────

async def get_advisor_recommendations(category: str | None = None) -> dict[str, Any]:
    """
    Fetch all Advisor recommendations, optionally filtered by category.
    category: 'Cost' | 'Security' | 'Reliability' | 'Performance' | 'OperationalExcellence'
    """
    loop = asyncio.get_event_loop()
    try:
        raw = await loop.run_in_executor(None, _fetch_recommendations)
    except Exception as e:
        return {"error": str(e), "status": "unknown", "recommendations": []}

    parsed = [_parse_recommendation(r) for r in raw]

    if category:
        parsed = [r for r in parsed if r["category"].lower() == category.lower()]

    # Sort by impact: High → Medium → Low
    order = {"High": 0, "Medium": 1, "Low": 2}
    parsed.sort(key=lambda r: order.get(r["impact"], 3))

    high   = [r for r in parsed if r["impact"] == "High"]
    medium = [r for r in parsed if r["impact"] == "Medium"]
    low    = [r for r in parsed if r["impact"] == "Low"]

    status = "critical" if high else "warning" if medium else "ok"

    return {
        "tool":    "get_advisor_recommendations",
        "category_filter": category or "all",
        "total":   len(parsed),
        "high":    len(high),
        "medium":  len(medium),
        "low":     len(low),
        "status":  status,
        "recommendations": parsed[:20],  # cap to avoid token overflow
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def get_advisor_cost_recommendations() -> dict[str, Any]:
    """Cost-saving recommendations — rightsizing, unused resources, reservations."""
    result = await get_advisor_recommendations(category="Cost")
    # Sum potential savings where available
    savings = sum(
        float(r["potential_savings_usd"])
        for r in result.get("recommendations", [])
        if r.get("potential_savings_usd") is not None
    )
    result["total_potential_savings_usd"] = round(savings, 2)
    result["tool"] = "get_advisor_cost_recommendations"
    return result


async def get_advisor_security_recommendations() -> dict[str, Any]:
    """Security posture recommendations from Azure Advisor."""
    result = await get_advisor_recommendations(category="Security")
    result["tool"] = "get_advisor_security_recommendations"
    return result


async def get_advisor_reliability_recommendations() -> dict[str, Any]:
    """High availability and reliability recommendations."""
    result = await get_advisor_recommendations(category="Reliability")
    result["tool"] = "get_advisor_reliability_recommendations"
    return result


async def get_advisor_summary() -> dict[str, Any]:
    """
    Composite summary across all Advisor categories — used by agents.
    Fetches once and splits by category to avoid multiple API calls.
    """
    loop = asyncio.get_event_loop()
    try:
        raw = await loop.run_in_executor(None, _fetch_recommendations)
    except Exception as e:
        return {
            "error": str(e),
            "overall_status": "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    parsed = [_parse_recommendation(r) for r in raw]
    order = {"High": 0, "Medium": 1, "Low": 2}
    parsed.sort(key=lambda r: order.get(r["impact"], 3))

    by_category: dict[str, list] = {}
    for r in parsed:
        by_category.setdefault(r["category"], []).append(r)

    summary = {}
    for cat, recs in by_category.items():
        high   = sum(1 for r in recs if r["impact"] == "High")
        medium = sum(1 for r in recs if r["impact"] == "Medium")
        summary[cat.lower()] = {
            "total":  len(recs),
            "high":   high,
            "medium": medium,
            "status": "critical" if high else "warning" if medium else "ok",
            "top_recommendations": recs[:3],
        }

    all_highs = sum(1 for r in parsed if r["impact"] == "High")
    all_meds  = sum(1 for r in parsed if r["impact"] == "Medium")
    overall   = "critical" if all_highs else "warning" if all_meds else "ok"

    return {
        "tool":            "get_advisor_summary",
        "total":           len(parsed),
        "high":            all_highs,
        "medium":          all_meds,
        "overall_status":  overall,
        "by_category":     summary,
        "timestamp":       datetime.now(timezone.utc).isoformat(),
    }
