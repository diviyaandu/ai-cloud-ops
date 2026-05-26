"""
tools/azure_cost.py

FinOps tool — Azure Cost Management API.

# ╔══════════════════════════════════════════════════════════════╗
# ║  LIVE MODE — reads real Azure Cost Management data           ║
# ║  Requires:                                                   ║
# ║    pip install azure-mgmt-costmanagement azure-identity      ║
# ║  Env vars: AZURE_SUBSCRIPTION_ID, AZURE_TENANT_ID,          ║
# ║            AZURE_CLIENT_ID, AZURE_CLIENT_SECRET              ║
# ║  To revert to mock: flip USE_REAL_AZURE = False              ║
# ╚══════════════════════════════════════════════════════════════╝
"""

import os
import random
from datetime import date, timedelta, datetime, timezone
from typing import Any

# ── Toggle ─────────────────────────────────────────────────────────────────────
USE_REAL_AZURE = True

AZURE_SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID", "")
AZURE_TENANT_ID       = os.getenv("AZURE_TENANT_ID", "")
AZURE_CLIENT_ID       = os.getenv("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET   = os.getenv("AZURE_CLIENT_SECRET", "")


# ── Credential helper (cached) ─────────────────────────────────────────────────
_credential = None

def _get_credential():
    global _credential
    if _credential is None:
        from azure.identity import ClientSecretCredential
        _credential = ClientSecretCredential(
            tenant_id=AZURE_TENANT_ID,
            client_id=AZURE_CLIENT_ID,
            client_secret=AZURE_CLIENT_SECRET,
        )
    return _credential


# ── Public API ─────────────────────────────────────────────────────────────────

async def get_monthly_spend() -> dict[str, Any]:
    """Return total spend for the current calendar month, by service."""
    if USE_REAL_AZURE:
        return await _real_monthly_spend()
    return _mock_monthly_spend()


async def get_daily_spend(days: int = 7) -> dict[str, Any]:
    """Return daily spend for the last N days."""
    if USE_REAL_AZURE:
        return await _real_daily_spend(days)
    return _mock_daily_spend(days)


async def get_cost_by_resource_group() -> dict[str, Any]:
    """Return spend broken down by resource group."""
    if USE_REAL_AZURE:
        return await _real_cost_by_resource_group()
    return _mock_cost_by_resource_group()


async def get_budget_status() -> dict[str, Any]:
    """Return current budget vs actual spend."""
    if USE_REAL_AZURE:
        return await _real_budget_status()
    return _mock_budget_status()


async def get_cost_anomalies() -> dict[str, Any]:
    """Detect spend spikes vs 30-day rolling average."""
    if USE_REAL_AZURE:
        return await _real_cost_anomalies()
    return _mock_cost_anomalies()


async def get_full_cost_report() -> dict[str, Any]:
    """Fetch all cost data in one call. Used by the FinOps Agent."""
    import asyncio
    monthly, daily, by_rg, budget, anomalies = await asyncio.gather(
        get_monthly_spend(),
        get_daily_spend(7),
        get_cost_by_resource_group(),
        get_budget_status(),
        get_cost_anomalies(),
        return_exceptions=True,
    )
    results = {}
    for label, val in [
        ("monthly_spend",    monthly),
        ("daily_spend_7d",   daily),
        ("by_resource_group", by_rg),
        ("budget_status",    budget),
        ("anomalies",        anomalies),
    ]:
        results[label] = {"error": str(val)} if isinstance(val, Exception) else val

    results["mode"] = "mock" if not USE_REAL_AZURE else "live"
    return results


# ── Real Azure implementations ─────────────────────────────────────────────────

def _run_cost_query(query_def) -> list:
    """Execute a Cost Management query synchronously (called via executor)."""
    from azure.mgmt.costmanagement import CostManagementClient
    client = CostManagementClient(_get_credential())
    scope = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}"
    result = client.query.usage(scope, query_def)
    return result.rows or []


async def _real_monthly_spend() -> dict[str, Any]:
    import asyncio
    from azure.mgmt.costmanagement.models import (
        QueryDefinition, QueryDataset, QueryAggregation,
        QueryGrouping, TimeframeType,
    )

    query = QueryDefinition(
        type="ActualCost",
        timeframe=TimeframeType.MONTH_TO_DATE,
        dataset=QueryDataset(
            granularity="None",
            aggregation={"totalCost": QueryAggregation(name="Cost", function="Sum")},
            grouping=[QueryGrouping(type="Dimension", name="ServiceName")],
        ),
    )

    loop = asyncio.get_event_loop()
    rows = await loop.run_in_executor(None, _run_cost_query, query)

    # rows = [[cost, currency, serviceName], ...]
    services = {}
    currency = "USD"
    for row in rows:
        cost, curr, service = float(row[0]), row[1], row[2]
        currency = curr
        if service:
            services[service] = round(cost, 2)

    total = round(sum(services.values()), 2)
    return {
        "metric":   "monthly_spend",
        "period":   f"{date.today().replace(day=1)} to {date.today()}",
        "currency": currency,
        "total":    total,
        "by_service": [
            {"service": k, "cost": v, "pct": round(v / total * 100, 1) if total else 0}
            for k, v in sorted(services.items(), key=lambda x: -x[1])
        ],
        "mode": "live",
    }


async def _real_daily_spend(days: int) -> dict[str, Any]:
    import asyncio
    from azure.mgmt.costmanagement.models import (
        QueryDefinition, QueryDataset, QueryAggregation,
        QueryTimePeriod, TimeframeType,
    )

    end   = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=days)

    query = QueryDefinition(
        type="ActualCost",
        timeframe=TimeframeType.CUSTOM,
        time_period=QueryTimePeriod(from_property=start, to=end),
        dataset=QueryDataset(
            granularity="Daily",
            aggregation={"totalCost": QueryAggregation(name="Cost", function="Sum")},
        ),
    )

    loop = asyncio.get_event_loop()
    rows = await loop.run_in_executor(None, _run_cost_query, query)

    # rows = [[cost, usageDate, currency], ...]
    daily = []
    currency = "USD"
    for row in rows:
        cost, usage_date, curr = float(row[0]), str(row[1]), row[2]
        currency = curr
        # usageDate comes back as int YYYYMMDD or string
        if len(usage_date) == 8:
            usage_date = f"{usage_date[:4]}-{usage_date[4:6]}-{usage_date[6:]}"
        daily.append({"date": usage_date, "cost": round(cost, 2), "currency": currency})

    daily.sort(key=lambda x: x["date"])
    avg = round(sum(d["cost"] for d in daily) / len(daily), 2) if daily else 0
    return {
        "metric":        "daily_spend",
        "days":          days,
        "data":          daily,
        "average_daily": avg,
        "mode":          "live",
    }


async def _real_cost_by_resource_group() -> dict[str, Any]:
    import asyncio
    from azure.mgmt.costmanagement.models import (
        QueryDefinition, QueryDataset, QueryAggregation,
        QueryGrouping, TimeframeType,
    )

    query = QueryDefinition(
        type="ActualCost",
        timeframe=TimeframeType.MONTH_TO_DATE,
        dataset=QueryDataset(
            granularity="None",
            aggregation={"totalCost": QueryAggregation(name="Cost", function="Sum")},
            grouping=[QueryGrouping(type="Dimension", name="ResourceGroupName")],
        ),
    )

    loop = asyncio.get_event_loop()
    rows = await loop.run_in_executor(None, _run_cost_query, query)

    groups = {}
    currency = "USD"
    for row in rows:
        cost, curr, rg = float(row[0]), row[1], row[2]
        currency = curr
        if rg:
            groups[rg] = round(cost, 2)

    total = round(sum(groups.values()), 2)
    return {
        "metric":   "cost_by_resource_group",
        "currency": currency,
        "total":    total,
        "by_resource_group": [
            {"resource_group": k, "cost": v, "pct": round(v / total * 100, 1) if total else 0}
            for k, v in sorted(groups.items(), key=lambda x: -x[1])
        ],
        "mode": "live",
    }


async def _real_budget_status() -> dict[str, Any]:
    """
    Fetch budgets from Azure Consumption API.
    Student accounts may not have budgets set — returns a 'no_budget' status gracefully.
    """
    import asyncio

    def _fetch():
        from azure.mgmt.consumption import ConsumptionManagementClient
        client = ConsumptionManagementClient(_get_credential(), AZURE_SUBSCRIPTION_ID)
        scope  = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}"
        return list(client.budgets.list(scope))

    loop = asyncio.get_event_loop()
    try:
        budgets = await loop.run_in_executor(None, _fetch)
    except Exception as e:
        # Student accounts often lack billing access — return graceful degradation
        return {
            "metric": "budget_status",
            "status": "unavailable",
            "note":   f"Budget API not accessible on this subscription: {e}",
            "mode":   "live",
        }

    if not budgets:
        return {
            "metric": "budget_status",
            "status": "no_budget_configured",
            "note":   "No budgets found. Set one in Azure Cost Management.",
            "mode":   "live",
        }

    # Use the first budget found
    b = budgets[0]
    budget_amount = float(b.amount)
    spent         = float(b.current_spend.amount) if b.current_spend else 0.0
    pct           = round(spent / budget_amount * 100, 1) if budget_amount else 0
    days_elapsed  = date.today().day
    days_in_month = 30
    expected_pct  = round(days_elapsed / days_in_month * 100, 1)
    on_track      = pct <= expected_pct + 10

    return {
        "metric":           "budget_status",
        "budget_name":      b.name,
        "budget_usd":       budget_amount,
        "spent_usd":        round(spent, 2),
        "remaining_usd":    round(budget_amount - spent, 2),
        "percent_used":     pct,
        "days_elapsed":     days_elapsed,
        "expected_percent": expected_pct,
        "on_track":         on_track,
        "status":           "ok" if on_track else "warning",
        "forecast_month_end": round(spent / days_elapsed * days_in_month, 2) if days_elapsed else 0,
        "mode": "live",
    }


async def _real_cost_anomalies() -> dict[str, Any]:
    """
    Detect anomalies by comparing last 7-day average daily spend vs prior 23 days.
    A day is flagged if its cost is >50% above the baseline average.
    """
    import asyncio
    from azure.mgmt.costmanagement.models import (
        QueryDefinition, QueryDataset, QueryAggregation,
        QueryTimePeriod, TimeframeType,
    )

    end   = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=30)

    query = QueryDefinition(
        type="ActualCost",
        timeframe=TimeframeType.CUSTOM,
        time_period=QueryTimePeriod(from_property=start, to=end),
        dataset=QueryDataset(
            granularity="Daily",
            aggregation={"totalCost": QueryAggregation(name="Cost", function="Sum")},
        ),
    )

    loop = asyncio.get_event_loop()
    rows = await loop.run_in_executor(None, _run_cost_query, query)

    daily = []
    for row in rows:
        cost, usage_date = float(row[0]), str(row[1])
        if len(usage_date) == 8:
            usage_date = f"{usage_date[:4]}-{usage_date[4:6]}-{usage_date[6:]}"
        daily.append({"date": usage_date, "cost": round(cost, 2)})

    daily.sort(key=lambda x: x["date"])

    if len(daily) < 8:
        return {
            "metric":            "cost_anomalies",
            "lookback_days":     30,
            "anomalies":         [],
            "total_anomaly_cost": 0,
            "status":            "ok",
            "note":              "Not enough data for anomaly detection yet.",
            "mode":              "live",
        }

    baseline_days  = daily[:-7]
    recent_days    = daily[-7:]
    baseline_avg   = sum(d["cost"] for d in baseline_days) / len(baseline_days)

    anomalies = []
    for day in recent_days:
        if baseline_avg > 0 and day["cost"] > baseline_avg * 1.5:
            delta_pct = round((day["cost"] - baseline_avg) / baseline_avg * 100, 1)
            anomalies.append({
                "date":          day["date"],
                "actual_cost":   day["cost"],
                "expected_cost": round(baseline_avg, 2),
                "delta_pct":     delta_pct,
                "severity":      "critical" if delta_pct > 100 else "warning",
            })

    return {
        "metric":             "cost_anomalies",
        "lookback_days":      30,
        "baseline_avg_daily": round(baseline_avg, 2),
        "anomalies":          anomalies,
        "total_anomaly_cost": round(sum(a["actual_cost"] - a["expected_cost"] for a in anomalies), 2),
        "status":             "warning" if anomalies else "ok",
        "mode":               "live",
    }


# ── Mock implementations (kept for USE_REAL_AZURE = False) ────────────────────

def _mock_monthly_spend() -> dict[str, Any]:
    services = {
        "Virtual Machines":          1842.50,
        "Azure Kubernetes Service":   934.20,
        "Azure SQL Database":         412.75,
        "Storage Accounts":           287.40,
        "Azure Monitor":              156.90,
        "Key Vault":                   42.10,
        "Bandwidth":                  198.60,
        "Load Balancer":               88.30,
    }
    total = sum(services.values())
    return {
        "metric": "monthly_spend",
        "period": f"{date.today().replace(day=1)} to {date.today()}",
        "currency": "USD",
        "total": round(total, 2),
        "by_service": [
            {"service": k, "cost": v, "pct": round(v / total * 100, 1)}
            for k, v in sorted(services.items(), key=lambda x: -x[1])
        ],
        "mode": "mock",
    }


def _mock_daily_spend(days: int) -> dict[str, Any]:
    base = 128.0
    daily = []
    for i in range(days, 0, -1):
        day = date.today() - timedelta(days=i)
        multiplier = 0.6 if day.weekday() >= 5 else 1.0
        cost = round(base * multiplier * random.uniform(0.85, 1.20), 2)
        daily.append({"date": str(day), "cost": cost, "currency": "USD"})
    return {
        "metric": "daily_spend", "days": days, "data": daily,
        "average_daily": round(sum(d["cost"] for d in daily) / len(daily), 2),
        "mode": "mock",
    }


def _mock_cost_by_resource_group() -> dict[str, Any]:
    groups = {
        "rg-production": 2187.40, "rg-staging": 643.90,
        "rg-dev": 298.70, "rg-monitoring": 312.55, "rg-networking": 520.80,
    }
    total = sum(groups.values())
    return {
        "metric": "cost_by_resource_group", "currency": "USD", "total": round(total, 2),
        "by_resource_group": [
            {"resource_group": k, "cost": v, "pct": round(v / total * 100, 1)}
            for k, v in sorted(groups.items(), key=lambda x: -x[1])
        ],
        "mode": "mock",
    }


def _mock_budget_status() -> dict[str, Any]:
    budget, spent = 5000.0, 3963.35
    pct = round(spent / budget * 100, 1)
    days_elapsed = date.today().day
    days_in_month = 30
    expected_pct = round(days_elapsed / days_in_month * 100, 1)
    on_track = pct <= expected_pct + 10
    return {
        "metric": "budget_status", "budget_usd": budget, "spent_usd": spent,
        "remaining_usd": round(budget - spent, 2), "percent_used": pct,
        "days_elapsed": days_elapsed, "expected_percent": expected_pct,
        "on_track": on_track, "status": "ok" if on_track else "warning",
        "forecast_month_end": round(spent / days_elapsed * days_in_month, 2),
        "mode": "mock",
    }


def _mock_cost_anomalies() -> dict[str, Any]:
    anomalies = [{
        "date": str(date.today() - timedelta(days=2)),
        "service": "Virtual Machines", "actual_cost": 312.40,
        "expected_cost": 180.50, "delta_pct": 73.1, "severity": "warning",
        "likely_cause": "Unexpected scale-out event — 4 extra VMs ran for 8h",
    }]
    return {
        "metric": "cost_anomalies", "lookback_days": 30, "anomalies": anomalies,
        "total_anomaly_cost": sum(a["actual_cost"] - a["expected_cost"] for a in anomalies),
        "status": "warning" if anomalies else "ok", "mode": "mock",
    }