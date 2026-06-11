"""
routes/resource_operations.py

GET /resource-operations
Returns a flat list of all resources with name, type, resource group,
location, and state — for the Resource Operations dashboard page.
Reuses get_resource_inventory() which already fetches this data.
"""
from fastapi import APIRouter
from tools.azure_resource_graph import get_resource_inventory

router = APIRouter()

@router.get("/resource-operations")
async def resource_operations():
    inventory = await get_resource_inventory()
    flat: list[dict] = []
    for group in inventory.get("by_type", []):
        for r in group.get("resources", []):
            flat.append({
                "id":             r.get("id", ""),
                "name":           r.get("name", ""),
                "type":           r.get("type", ""),
                "resource_group": r.get("resource_group", ""),
                "location":       r.get("location", ""),
                "state":          r.get("state", ""),
            })
    return {
        "total": len(flat),
        "mode":  inventory.get("mode", "unknown"),
        "resources": flat,
    }