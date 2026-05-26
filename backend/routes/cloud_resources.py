"""
routes/cloud_resources.py

GET /cloud-resources
Returns a normalized cloud resource inventory summary for the dashboard stat cards.
Pulls from Azure Resource Graph via the existing tool.
"""

from fastapi import APIRouter
from tools.azure_resource_graph import get_resource_inventory

router = APIRouter()

RESOURCE_TYPE_MAP = {
    "microsoft.compute/virtualmachines":          "virtual_machines",
    "microsoft.containerservice/managedclusters": "aks_clusters",
    "microsoft.web/sites":                        "app_services",
    "microsoft.storage/storageaccounts":          "storage_accounts",
}


@router.get("/cloud-resources")
async def cloud_resources():
    """
    Returns:
      {
        "total": int,
        "virtual_machines": int,
        "aks_clusters": int,
        "app_services": int,
        "storage_accounts": int,
        "mode": "live" | "mock",
        "raw_by_type": [...]   ← full breakdown for future use
      }
    """
    inventory = await get_resource_inventory()

    counts = {
        "virtual_machines": 0,
        "aks_clusters":     0,
        "app_services":     0,
        "storage_accounts": 0,
    }

    for entry in inventory.get("by_type", []):
        key = RESOURCE_TYPE_MAP.get(entry["type"].lower())
        if key:
            counts[key] += entry["count"]

    return {
        "total":            inventory.get("total_resources", 0),
        **counts,
        "mode":             inventory.get("mode", "unknown"),
        "raw_by_type":      inventory.get("by_type", []),
    }