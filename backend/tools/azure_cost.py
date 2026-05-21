"""
tools/azure_cost.py

FinOps tool — Azure Cost Management API.

# ╔══════════════════════════════════════════════════════════════╗
# ║  MOCK MODE — returns realistic fake data                     ║
# ║  To swap to real Azure:                                      ║
# ║    1. pip install azure-mgmt-costmanagement azure-identity   ║
# ║    2. Set env vars: AZURE_SUBSCRIPTION_ID, AZURE_TENANT_ID, ║
# ║       AZURE_CLIENT_ID, AZURE_CLIENT_SECRET                   ║
# ║    3. Flip USE_REAL_AZURE = True below                       ║
# ║    4. Delete the _mock_* functions                           ║
# ╚══════════════════════════════════════════════════════════════╝
"""

import os
import random
from datetime import date, timedelta
from typing import Any

# ── Toggle ─────────────────────────────────────────────────────────────────────
USE_REAL_AZURE = False  # TODO: flip to True when credentials are configured

AZURE_SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID", "")
AZURE_TENANT_ID       = os.getenv("AZURE_TENANT_ID", "")
AZURE_CLIENT_ID       = os.getenv("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET   = os.getenv("AZURE_CLIENT_SECRET", "")


# ── Public API (same shape whether real or mock) ───────────────────────────────

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
        ("monthly_spend", monthly),
        ("daily_spend_7d", daily),
        ("by_resource_group", by_rg),
        ("budget_status", budget),
        ("anomalies", anomalies),
    ]:
        results[label] = {"error": str(val)} if isinstance(val, Exception) else val

    results["mode"] = "mock" if not USE_REAL_AZURE else "live"
    return results


# ── Mock implementations ───────────────────────────────────────────────────────

def _mock_monthly_spend() -> dict[str, Any]:
    services = {
        "Virtual Machines":         1842.50,
        "Azure Kubernetes Service":  934.20,
        "Azure SQL Database":        412.75,
        "Storage Accounts":          287.40,
        "Azure Monitor":             156.90,
        "Key Vault":                  42.10,
        "Bandwidth":                 198.60,
        "Load Balancer":              88.30,
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
        # Simulate weekday/weekend pattern + some noise
        multiplier = 0.6 if day.weekday() >= 5 else 1.0
        cost = round(base * multiplier * random.uniform(0.85, 1.20), 2)
        daily.append({"date": str(day), "cost": cost, "currency": "USD"})
    return {
        "metric": "daily_spend",
        "days": days,
        "data": daily,
        "average_daily": round(sum(d["cost"] for d in daily) / len(daily), 2),
        "mode": "mock",
    }


def _mock_cost_by_resource_group() -> dict[str, Any]:
    groups = {
        "rg-production":   2187.40,
        "rg-staging":       643.90,
        "rg-dev":           298.70,
        "rg-monitoring":    312.55,
        "rg-networking":    520.80,
    }
    total = sum(groups.values())
    return {
        "metric": "cost_by_resource_group",
        "currency": "USD",
        "total": round(total, 2),
        "by_resource_group": [
            {"resource_group": k, "cost": v, "pct": round(v / total * 100, 1)}
            for k, v in sorted(groups.items(), key=lambda x: -x[1])
        ],
        "mode": "mock",
    }


def _mock_budget_status() -> dict[str, Any]:
    budget = 5000.0
    spent = 3963.35
    pct = round(spent / budget * 100, 1)
    days_elapsed = date.today().day
    days_in_month = 30
    expected_pct = round(days_elapsed / days_in_month * 100, 1)
    on_track = pct <= expected_pct + 10

    return {
        "metric": "budget_status",
        "budget_usd": budget,
        "spent_usd": spent,
        "remaining_usd": round(budget - spent, 2),
        "percent_used": pct,
        "days_elapsed": days_elapsed,
        "expected_percent": expected_pct,
        "on_track": on_track,
        "status": "ok" if on_track else "warning",
        "forecast_month_end": round(spent / days_elapsed * days_in_month, 2),
        "mode": "mock",
    }


def _mock_cost_anomalies() -> dict[str, Any]:
    anomalies = [
        {
            "date": str(date.today() - timedelta(days=2)),
            "service": "Virtual Machines",
            "actual_cost": 312.40,
            "expected_cost": 180.50,
            "delta_pct": 73.1,
            "severity": "warning",
            "likely_cause": "Unexpected scale-out event — 4 extra VMs ran for 8h",
        }
    ]
    return {
        "metric": "cost_anomalies",
        "lookback_days": 30,
        "anomalies": anomalies,
        "total_anomaly_cost": sum(a["actual_cost"] - a["expected_cost"] for a in anomalies),
        "status": "warning" if anomalies else "ok",
        "mode": "mock",
    }


# ── Real Azure implementations ─────────────────────────────────────────────────
# TODO: uncomment and implement when Azure credentials are ready

async def _real_monthly_spend() -> dict[str, Any]:
    # from azure.identity import ClientSecretCredential
    # from azure.mgmt.costmanagement import CostManagementClient
    # from azure.mgmt.costmanagement.models import (
    #     QueryDefinition, QueryTimePeriod, QueryDataset,
    #     QueryAggregation, QueryGrouping, TimeframeType,
    # )
    # credential = ClientSecretCredential(AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET)
    # client = CostManagementClient(credential)
    # scope = f"/subscriptions/{AZURE_SUBSCRIPTION_ID}"
    # query = QueryDefinition(
    #     type="ActualCost",
    #     timeframe=TimeframeType.MONTH_TO_DATE,
    #     dataset=QueryDataset(
    #         granularity="None",
    #         aggregation={"totalCost": QueryAggregation(name="Cost", function="Sum")},
    #         grouping=[QueryGrouping(type="Dimension", name="ServiceName")],
    #     ),
    # )
    # result = client.query.usage(scope, query)
    # ... parse result.rows into the same shape as _mock_monthly_spend()
    raise NotImplementedError("Set USE_REAL_AZURE = True and implement this function")


async def _real_daily_spend(days: int) -> dict[str, Any]:
    raise NotImplementedError("TODO: implement real Azure daily spend query")


async def _real_cost_by_resource_group() -> dict[str, Any]:
    raise NotImplementedError("TODO: implement real Azure resource group cost query")


async def _real_budget_status() -> dict[str, Any]:
    raise NotImplementedError("TODO: implement real Azure budget API query")


async def _real_cost_anomalies() -> dict[str, Any]:
    raise NotImplementedError("TODO: implement real Azure cost anomaly detection")