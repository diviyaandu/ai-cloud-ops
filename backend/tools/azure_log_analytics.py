"""
tools/azure_log_analytics.py

Log Analytics toolbox — queries Azure Log Analytics workspace via the REST API.

Workspace: law-finopsai-dev (rg-finopsai-dev, eastus)
Set AZURE_LOG_ANALYTICS_WORKSPACE_ID in your .env to your workspace's customerId GUID.

Queries available:
  - get_recent_errors        : Application exceptions/errors in last 24h
  - get_recent_warnings      : Warning-level events in last 24h
  - get_resource_health_logs : Azure activity log health events
  - get_top_operations       : Most frequent Azure operations in last 24h
  - get_failed_operations    : Failed Azure resource operations in last 24h
  - get_log_summary          : Composite summary (all of the above)
"""

import os
import asyncio
import requests
from datetime import datetime, timezone
from typing import Any

WORKSPACE_ID = os.getenv("AZURE_LOG_ANALYTICS_WORKSPACE_ID", "")
QUERY_URL = f"https://api.loganalytics.io/v1/workspaces/{WORKSPACE_ID}/query"

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


def _run_query(kql: str, timespan: str = "P1D") -> list[dict]:
    """
    Execute a KQL query against the Log Analytics workspace.
    timespan: ISO 8601 duration — P1D = last 24h, PT1H = last 1h, P7D = last 7 days
    Returns a list of row dicts.
    """
    if not WORKSPACE_ID:
        raise RuntimeError(
            "AZURE_LOG_ANALYTICS_WORKSPACE_ID not set. "
            "Add it to your .env file."
        )

    token = _get_credential().get_token("https://api.loganalytics.io/.default").token

    resp = requests.post(
        QUERY_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"query": kql, "timespan": timespan},
        timeout=30,
    )

    if not resp.ok:
        raise RuntimeError(
            f"Log Analytics query failed ({resp.status_code}): {resp.text[:300]}"
        )

    data = resp.json()
    tables = data.get("tables", [])
    if not tables:
        return []

    table = tables[0]
    columns = [c["name"] for c in table["columns"]]
    return [dict(zip(columns, row)) for row in table["rows"]]


def _safe_query(kql: str, timespan: str = "P1D") -> list[dict]:
    """Run query and return empty list on error (for gather calls)."""
    try:
        return _run_query(kql, timespan)
    except Exception:
        return []


# ── Public tool functions ──────────────────────────────────────────────────────

async def get_recent_errors() -> dict[str, Any]:
    """Exceptions and errors from App Insights / Azure diagnostics in last 24h."""
    kql = """
        union isfuzzy=true
            (AppExceptions | project TimeGenerated, Message=OuterMessage,
             SeverityLevel, ResourceId=AppRoleName, Source="AppInsights"),
            (AzureDiagnostics | where Level == "Error"
             | project TimeGenerated, Message=ResultDescription,
               SeverityLevel=3, ResourceId, Source="AzureDiagnostics")
        | where TimeGenerated > ago(24h)
        | order by TimeGenerated desc
        | limit 20
    """
    loop = asyncio.get_event_loop()
    rows = await loop.run_in_executor(None, _safe_query, kql, "P1D")

    return {
        "tool": "get_recent_errors",
        "window": "24h",
        "total": len(rows),
        "errors": rows,
        "status": "critical" if len(rows) > 10 else "warning" if rows else "ok",
        "summary": f"{len(rows)} error(s) in last 24h",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def get_recent_warnings() -> dict[str, Any]:
    """Warning-level events from Azure diagnostics in last 24h."""
    kql = """
        AzureDiagnostics
        | where Level == "Warning" and TimeGenerated > ago(24h)
        | project TimeGenerated, ResourceType, ResourceGroup,
                  Message=ResultDescription, OperationName
        | order by TimeGenerated desc
        | limit 20
    """
    loop = asyncio.get_event_loop()
    rows = await loop.run_in_executor(None, _safe_query, kql, "P1D")

    return {
        "tool": "get_recent_warnings",
        "window": "24h",
        "total": len(rows),
        "warnings": rows,
        "status": "warning" if rows else "ok",
        "summary": f"{len(rows)} warning(s) in last 24h",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def get_resource_health_logs() -> dict[str, Any]:
    """Azure Activity Log health and availability events in last 24h."""
    kql = """
        AzureActivity
        | where TimeGenerated > ago(24h)
        | where CategoryValue == "ResourceHealth" or Level in ("Critical", "Error", "Warning")
        | project TimeGenerated, ResourceGroup, ResourceProviderValue,
                  ResourceId = _ResourceId, ResourceName = tolower(split(_ResourceId, "/")[-1]),
                  ActivityStatusValue, OperationNameValue, Level, Caller, Properties
        | order by TimeGenerated desc
        | limit 25
    """
    loop = asyncio.get_event_loop()
    rows = await loop.run_in_executor(None, _safe_query, kql, "P1D")

    critical = [r for r in rows if r.get("Level") == "Critical"]
    errors    = [r for r in rows if r.get("Level") == "Error"]

    status = "critical" if critical else "warning" if errors else "ok"

    return {
        "tool": "get_resource_health_logs",
        "window": "24h",
        "total": len(rows),
        "critical_count": len(critical),
        "error_count": len(errors),
        "events": rows,
        "status": status,
        "summary": f"{len(rows)} health event(s) — {len(critical)} critical, {len(errors)} errors",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def get_top_operations() -> dict[str, Any]:
    """Most frequent Azure operations in last 24h (activity log)."""
    kql = """
        AzureActivity
        | where TimeGenerated > ago(24h)
        | summarize count() by OperationNameValue, ResourceProviderValue, ActivityStatusValue
        | order by count_ desc
        | limit 15
    """
    loop = asyncio.get_event_loop()
    rows = await loop.run_in_executor(None, _safe_query, kql, "P1D")

    return {
        "tool": "get_top_operations",
        "window": "24h",
        "total_distinct_operations": len(rows),
        "operations": rows,
        "status": "ok",
        "summary": f"Top {len(rows)} operations in last 24h",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def get_failed_operations() -> dict[str, Any]:
    """Failed Azure resource operations in last 24h."""
    kql = """
        AzureActivity
        | where TimeGenerated > ago(24h)
        | where ActivityStatusValue in ("Failed", "Failure")
        | project TimeGenerated, ResourceGroup, ResourceProviderValue,
                  OperationNameValue, ActivityStatusValue, Caller, Properties
        | order by TimeGenerated desc
        | limit 20
    """
    loop = asyncio.get_event_loop()
    rows = await loop.run_in_executor(None, _safe_query, kql, "P1D")

    return {
        "tool": "get_failed_operations",
        "window": "24h",
        "total": len(rows),
        "failures": rows,
        "status": "critical" if len(rows) > 5 else "warning" if rows else "ok",
        "summary": f"{len(rows)} failed operation(s) in last 24h",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def get_log_summary() -> dict[str, Any]:
    """Composite summary — all log checks in parallel. Used by agents."""
    errors_r, warnings_r, health_r, ops_r, failed_r = await asyncio.gather(
        get_recent_errors(),
        get_recent_warnings(),
        get_resource_health_logs(),
        get_top_operations(),
        get_failed_operations(),
        return_exceptions=True,
    )

    def _safe(r):
        return r if not isinstance(r, Exception) else {"error": str(r), "status": "unknown"}

    results = {
        "recent_errors":    _safe(errors_r),
        "recent_warnings":  _safe(warnings_r),
        "resource_health":  _safe(health_r),
        "top_operations":   _safe(ops_r),
        "failed_operations": _safe(failed_r),
    }

    statuses = [v.get("status", "ok") for v in results.values()]
    if "critical" in statuses:
        overall = "critical"
    elif "warning" in statuses:
        overall = "warning"
    elif "unknown" in statuses:
        overall = "unknown"
    else:
        overall = "ok"

    results["overall_status"] = overall
    results["timestamp"] = datetime.now(timezone.utc).isoformat()
    return results