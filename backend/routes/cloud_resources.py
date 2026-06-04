"""
routes/cloud_resources.py

GET /cloud-resources
Returns a normalized cloud resource inventory summary for the dashboard stat cards.
Pulls from Azure Resource Graph via the existing tool.
"""
from fastapi import APIRouter
from tools.azure_resource_graph import get_resource_inventory

router = APIRouter()

@router.get("/cloud-resources")
async def cloud_resources():
    inventory = await get_resource_inventory()
    by_type = inventory.get("by_type", [])
    return {
        "total":       inventory.get("total_resources", 0),
        "mode":        inventory.get("mode", "unknown"),
        "raw_by_type": by_type,
    }