"""
tools/azure_resource_graph.py

Azure Resource Graph tool — query and inventory Azure resources.

# ╔══════════════════════════════════════════════════════════════╗
# ║  LIVE MODE — reads real Azure Resource Graph data            ║
# ║  Requires:                                                   ║
# ║    pip install azure-mgmt-resourcegraph azure-identity       ║
# ║    pip install azure-mgmt-monitor (for recent changes)       ║
# ║  Env vars: AZURE_SUBSCRIPTION_ID, AZURE_TENANT_ID,          ║
# ║            AZURE_CLIENT_ID, AZURE_CLIENT_SECRET              ║
# ║  To revert to mock: flip USE_REAL_AZURE = False              ║
# ╚══════════════════════════════════════════════════════════════╝
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any
from dotenv import load_dotenv
load_dotenv()

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
            tenant_id=os.getenv("AZURE_TENANT_ID", ""),
            client_id=os.getenv("AZURE_CLIENT_ID", ""),
            client_secret=os.getenv("AZURE_CLIENT_SECRET", ""),
        )
    return _credential


def _graph_query(kql: str) -> list[dict]:
    import requests

    sub_id = os.getenv("AZURE_SUBSCRIPTION_ID", "")
    if not sub_id:
        raise ValueError("AZURE_SUBSCRIPTION_ID is not set")

    # Get token directly from credential
    token = _get_credential().get_token("https://management.azure.com/.default").token
    token = _get_credential().get_token("https://management.azure.com/.default").token
    import json, base64
    # Decode JWT payload (middle part)
    payload = token.split('.')[1]
    payload += '=' * (4 - len(payload) % 4)  # fix padding
    decoded = json.loads(base64.b64decode(payload))
    print(f"DEBUG token sub: {decoded.get('sub')}")
    print(f"DEBUG token oid: {decoded.get('oid')}")
    print(f"DEBUG token roles: {decoded.get('roles')}")
    print(f"DEBUG token scp: {decoded.get('scp')}")
    print(f"DEBUG token tid: {decoded.get('tid')}")
    resp = requests.post(
        "https://management.azure.com/providers/Microsoft.ResourceGraph/resources?api-version=2021-03-01",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "subscriptions": [sub_id],
            "query": kql,
        },
        timeout=30,
    )
    data = resp.json()
    print(f"DEBUG raw response: {data}")

    # REST API returns {data: [...]} not {columns, rows}
    rows_data = data.get("data", [])
    if rows_data and isinstance(rows_data[0], dict):
        # Already in dict format — return directly
        return rows_data

    # Fallback for column/row format
    columns = [c["name"] for c in data.get("columns", [])]
    return [dict(zip(columns, row)) for row in data.get("rows", [])]
# ── Public API ─────────────────────────────────────────────────────────────────

async def get_resource_inventory() -> dict[str, Any]:
    if USE_REAL_AZURE:
        return await _real_resource_inventory()
    return _mock_resource_inventory()


async def get_unhealthy_resources() -> dict[str, Any]:
    if USE_REAL_AZURE:
        return await _real_unhealthy_resources()
    return _mock_unhealthy_resources()


async def get_resource_group_summary() -> dict[str, Any]:
    if USE_REAL_AZURE:
        return await _real_resource_group_summary()
    return _mock_resource_group_summary()


async def get_recently_modified_resources(hours: int = 24) -> dict[str, Any]:
    if USE_REAL_AZURE:
        return await _real_recently_modified_resources(hours)
    return _mock_recently_modified_resources(hours)


async def get_untagged_resources() -> dict[str, Any]:
    if USE_REAL_AZURE:
        return await _real_untagged_resources()
    return _mock_untagged_resources()


async def get_full_resource_report() -> dict[str, Any]:
    import asyncio
    inventory, unhealthy, rg_summary, recent, untagged = await asyncio.gather(
        get_resource_inventory(),
        get_unhealthy_resources(),
        get_resource_group_summary(),
        get_recently_modified_resources(24),
        get_untagged_resources(),
        return_exceptions=True,
    )
    results = {}
    for label, val in [
        ("inventory",              inventory),
        ("unhealthy_resources",    unhealthy),
        ("resource_group_summary", rg_summary),
        ("recently_modified_24h",  recent),
        ("untagged_resources",     untagged),
    ]:
        results[label] = {"error": str(val)} if isinstance(val, Exception) else val
    results["mode"] = "mock" if not USE_REAL_AZURE else "live"
    return results


# ── Real Azure implementations ─────────────────────────────────────────────────

async def _real_resource_inventory() -> dict[str, Any]:
    import asyncio

    kql = """
        Resources
        | summarize count() by type, location
        | order by count_ desc
    """

    loop = asyncio.get_event_loop()
    rows = await loop.run_in_executor(None, _graph_query, kql)

    # Aggregate by type across locations
    by_type: dict[str, dict] = {}
    for row in rows:
        t = row.get("type", "unknown")
        loc = row.get("location", "unknown")
        cnt = int(row.get("count_", 0))
        if t not in by_type:
            by_type[t] = {"type": t, "count": 0, "regions": []}
        by_type[t]["count"] += cnt
        if loc not in by_type[t]["regions"]:
            by_type[t]["regions"].append(loc)

    sorted_types = sorted(by_type.values(), key=lambda x: -x["count"])
    total = sum(r["count"] for r in sorted_types)

    return {
        "metric":         "resource_inventory",
        "total_resources": total,
        "resource_types":  len(sorted_types),
        "by_type":         sorted_types,
        "mode":            "live",
    }


async def _real_unhealthy_resources() -> dict[str, Any]:
    import asyncio

    kql = """
        Resources
        | where properties.provisioningState != 'Succeeded'
              or properties.powerState.code == 'PowerState/deallocated'
        | project name, type, resourceGroup, location,
                  state = tostring(properties.provisioningState),
                  powerState = tostring(properties.powerState.code)
        | limit 50
    """

    loop = asyncio.get_event_loop()
    rows = await loop.run_in_executor(None, _graph_query, kql)

    resources = []
    for row in rows:
        state = row.get("state") or row.get("powerState") or "Unknown"
        severity = "critical" if state in ("Failed", "Canceled") else "warning"
        resources.append({
            "name":           row.get("name"),
            "type":           row.get("type"),
            "resource_group": row.get("resourceGroup"),
            "location":       row.get("location"),
            "state":          state,
            "severity":       severity,
        })

    critical_count = sum(1 for r in resources if r["severity"] == "critical")
    warning_count  = sum(1 for r in resources if r["severity"] == "warning")

    return {
        "metric":          "unhealthy_resources",
        "total_unhealthy": len(resources),
        "critical":        critical_count,
        "warning":         warning_count,
        "resources":       resources,
        "status":          "critical" if critical_count > 0 else "warning" if warning_count > 0 else "ok",
        "mode":            "live",
    }


async def _real_resource_group_summary() -> dict[str, Any]:
    import asyncio

    kql = """
        Resources
        | summarize resource_count = count(), types = make_set(type) by resourceGroup, location
        | order by resource_count desc
    """

    # Also get RG tags
    rg_kql = """
        ResourceContainers
        | where type == 'microsoft.resources/subscriptions/resourcegroups'
        | project name, location, tags
    """

    loop = asyncio.get_event_loop()
    resource_rows, rg_rows = await asyncio.gather(
        loop.run_in_executor(None, _graph_query, kql),
        loop.run_in_executor(None, _graph_query, rg_kql),
    )

    rg_tags = {r["name"]: r.get("tags") or {} for r in rg_rows}

    groups = []
    for row in resource_rows:
        rg = row.get("resourceGroup", "unknown")
        raw_types = row.get("types", [])
        # Shorten type names for readability
        short_types = list({t.split("/")[-1] for t in (raw_types if isinstance(raw_types, list) else [])})
        groups.append({
            "name":           rg,
            "resource_count": int(row.get("resource_count", 0)),
            "resource_types": short_types[:6],
            "location":       row.get("location"),
            "tags":           rg_tags.get(rg, {}),
        })

    return {
        "metric":                "resource_group_summary",
        "total_resource_groups": len(groups),
        "total_resources":       sum(g["resource_count"] for g in groups),
        "by_resource_group":     groups,
        "mode":                  "live",
    }


async def _real_recently_modified_resources(hours: int) -> dict[str, Any]:
    """
    Uses Azure Monitor Activity Log to find resources changed in the last N hours.
    Falls back gracefully if the Monitor SDK is not installed or access is denied.
    """
    import asyncio

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    filter_str = (
        f"eventTimestamp ge '{since.isoformat()}' "
        f"and eventTimestamp le '{datetime.now(timezone.utc).isoformat()}' "
        f"and status eq 'Succeeded'"
    )

    def _fetch():
        from azure.mgmt.monitor import MonitorManagementClient
        client = MonitorManagementClient(_get_credential(), os.getenv("AZURE_SUBSCRIPTION_ID", ""))
        events = list(client.activity_logs.list(
            filter=filter_str,
            select="eventTimestamp,operationName,resourceGroupName,resourceType,resourceId,caller,httpRequest",
        ))
        return events

    loop = asyncio.get_event_loop()
    try:
        events = await loop.run_in_executor(None, _fetch)
    except Exception as e:
        return {
            "metric":         "recently_modified_resources",
            "lookback_hours": hours,
            "total_changes":  0,
            "resources":      [],
            "note":           f"Activity log unavailable: {e}",
            "mode":           "live",
        }

    resources = []
    seen = set()
    for event in events:
        rid = getattr(event, "resource_id", None) or ""
        op  = getattr(event.operation_name, "value", "") if event.operation_name else ""
        # Only include write/delete ops, skip reads
        if not any(x in op.lower() for x in ["write", "delete", "action"]):
            continue
        if rid in seen:
            continue
        seen.add(rid)
        name = rid.split("/")[-1] if rid else "unknown"
        resources.append({
            "name":           name,
            "resource_id":    rid,
            "resource_group": getattr(event, "resource_group_name", ""),
            "operation":      op,
            "modified_at":    str(event.event_timestamp) if event.event_timestamp else "",
            "modified_by":    getattr(event, "caller", ""),
        })
        if len(resources) >= 20:
            break

    return {
        "metric":         "recently_modified_resources",
        "lookback_hours": hours,
        "total_changes":  len(resources),
        "resources":      resources,
        "mode":           "live",
    }


async def _real_untagged_resources() -> dict[str, Any]:
    import asyncio

    required_tags = ["owner", "env", "cost-center"]

    kql = """
        Resources
        | where isnull(tags.owner) or isnull(tags.env) or isnull(tags['cost-center'])
        | project name, type, resourceGroup, tags
        | limit 50
    """

    loop = asyncio.get_event_loop()
    rows = await loop.run_in_executor(None, _graph_query, kql)

    resources = []
    for row in rows:
        present = row.get("tags") or {}
        missing = [t for t in required_tags if t not in present or not present[t]]
        if missing:
            resources.append({
                "name":           row.get("name"),
                "type":           row.get("type"),
                "resource_group": row.get("resourceGroup"),
                "missing_tags":   missing,
                "present_tags":   present,
            })

    return {
        "metric":         "untagged_resources",
        "required_tags":  required_tags,
        "total_untagged": len(resources),
        "resources":      resources,
        "status":         "warning" if resources else "ok",
        "mode":           "live",
    }


# ── Mock implementations (kept for USE_REAL_AZURE = False) ────────────────────

def _mock_resource_inventory() -> dict[str, Any]:
    resources = [
        {"type": "Microsoft.Compute/virtualMachines",         "count": 12, "regions": ["eastus", "westeurope"]},
        {"type": "Microsoft.ContainerService/managedClusters","count": 2,  "regions": ["eastus"]},
        {"type": "Microsoft.Sql/servers",                     "count": 3,  "regions": ["eastus", "eastus2"]},
        {"type": "Microsoft.Storage/storageAccounts",         "count": 8,  "regions": ["eastus", "westus2", "westeurope"]},
        {"type": "Microsoft.Network/virtualNetworks",         "count": 4,  "regions": ["eastus", "westeurope"]},
        {"type": "Microsoft.Network/loadBalancers",           "count": 3,  "regions": ["eastus"]},
        {"type": "Microsoft.KeyVault/vaults",                 "count": 5,  "regions": ["eastus", "westeurope"]},
        {"type": "Microsoft.Insights/components",             "count": 4,  "regions": ["eastus"]},
        {"type": "Microsoft.Network/publicIPAddresses",       "count": 6,  "regions": ["eastus", "westeurope"]},
        {"type": "Microsoft.Web/sites",                       "count": 3,  "regions": ["eastus"]},
    ]
    total = sum(r["count"] for r in resources)
    return {"metric": "resource_inventory", "total_resources": total,
            "resource_types": len(resources), "by_type": sorted(resources, key=lambda x: -x["count"]), "mode": "mock"}


def _mock_unhealthy_resources() -> dict[str, Any]:
    now = datetime.utcnow()
    resources = [
        {"name": "vm-worker-03", "type": "Microsoft.Compute/virtualMachines",
         "resource_group": "rg-production", "state": "Failed",
         "issue": "Provisioning failed — insufficient quota in eastus",
         "since": str(now - timedelta(hours=3)), "severity": "critical"},
        {"name": "aks-node-pool-1", "type": "Microsoft.ContainerService/managedClusters",
         "resource_group": "rg-production", "state": "Degraded",
         "issue": "2 of 5 nodes NotReady — disk pressure",
         "since": str(now - timedelta(hours=1, minutes=12)), "severity": "warning"},
    ]
    critical_count = sum(1 for r in resources if r["severity"] == "critical")
    warning_count  = sum(1 for r in resources if r["severity"] == "warning")
    return {"metric": "unhealthy_resources", "total_unhealthy": len(resources),
            "critical": critical_count, "warning": warning_count, "resources": resources,
            "status": "critical" if critical_count > 0 else "warning" if warning_count > 0 else "ok", "mode": "mock"}


def _mock_resource_group_summary() -> dict[str, Any]:
    groups = [
        {"name": "rg-production", "resource_count": 28, "resource_types": ["VMs","AKS","SQL","Storage"],
         "location": "eastus", "tags": {"env": "prod", "cost-center": "engineering"}},
        {"name": "rg-staging", "resource_count": 14, "resource_types": ["VMs","SQL","Storage"],
         "location": "eastus", "tags": {"env": "staging"}},
        {"name": "rg-dev", "resource_count": 9, "resource_types": ["VMs","Storage"],
         "location": "eastus2", "tags": {"env": "dev"}},
    ]
    return {"metric": "resource_group_summary", "total_resource_groups": len(groups),
            "total_resources": sum(g["resource_count"] for g in groups),
            "by_resource_group": groups, "mode": "mock"}


def _mock_recently_modified_resources(hours: int) -> dict[str, Any]:
    now = datetime.utcnow()
    resources = [
        {"name": "vm-api-gateway-01", "type": "Microsoft.Compute/virtualMachines",
         "resource_group": "rg-production", "modified_at": str(now - timedelta(minutes=22)),
         "modified_by": "svc-deployer@company.com", "change_type": "Update",
         "details": "OS disk resized from 128GB to 256GB"},
    ]
    return {"metric": "recently_modified_resources", "lookback_hours": hours,
            "total_changes": len(resources), "resources": resources, "mode": "mock"}


def _mock_untagged_resources() -> dict[str, Any]:
    required_tags = ["owner", "env", "cost-center"]
    resources = [
        {"name": "vm-test-scratch-01", "type": "Microsoft.Compute/virtualMachines",
         "resource_group": "rg-dev", "missing_tags": ["owner", "cost-center"],
         "present_tags": {"env": "dev"}},
        {"name": "storage-tmp-uploads", "type": "Microsoft.Storage/storageAccounts",
         "resource_group": "rg-dev", "missing_tags": ["owner", "env", "cost-center"],
         "present_tags": {}},
    ]
    return {"metric": "untagged_resources", "required_tags": required_tags,
            "total_untagged": len(resources), "resources": resources,
            "status": "warning" if resources else "ok", "mode": "mock"}