from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.resource import ResourceManagementClient
import os

SUBSCRIPTION_ID = os.environ["AZURE_SUBSCRIPTION_ID"]
ALLOWED_RGS = set(os.getenv("AZURE_ALLOWED_RGS", "rg-finops-prod,rg-finopsai-dev").split(","))

def _credential():
    return ClientSecretCredential(
        tenant_id=os.environ["AZURE_TENANT_ID"],
        client_id=os.environ["AZURE_CLIENT_ID"],
        client_secret=os.environ["AZURE_CLIENT_SECRET"],
    )

def _check_rg(resource_group: str):
    if resource_group not in ALLOWED_RGS:
        raise ValueError(f"Resource group '{resource_group}' not in allowed list.")

def apply_tags(resource_id: str, tags: dict) -> dict:
    cred = _credential()
    client = ResourceManagementClient(cred, SUBSCRIPTION_ID)
    parts = resource_id.strip("/").split("/")
    rg = parts[parts.index("resourceGroups") + 1]
    _check_rg(rg)
    result = client.resources.get_by_id(resource_id, api_version="2021-04-01")
    merged = {**(result.tags or {}), **tags}
    updated = client.resources.begin_update_by_id(
        resource_id, "2021-04-01", {"tags": merged}
    ).result()
    return {"resource_id": resource_id, "tags": updated.tags}

def stop_vm(resource_group: str, vm_name: str) -> dict:
    _check_rg(resource_group)
    client = ComputeManagementClient(_credential(), SUBSCRIPTION_ID)
    client.virtual_machines.begin_deallocate(resource_group, vm_name).result()
    return {"action": "stop_vm", "vm": vm_name, "status": "deallocated"}

def start_vm(resource_group: str, vm_name: str) -> dict:
    _check_rg(resource_group)
    client = ComputeManagementClient(_credential(), SUBSCRIPTION_ID)
    client.virtual_machines.begin_start(resource_group, vm_name).result()
    return {"action": "start_vm", "vm": vm_name, "status": "started"}

def scale_app_service(resource_group: str, plan_name: str, sku_name: str, capacity: int) -> dict:
    _check_rg(resource_group)
    client = WebSiteManagementClient(_credential(), SUBSCRIPTION_ID)
    plan = client.app_service_plans.get(resource_group, plan_name)
    plan.sku.name = sku_name
    plan.sku.capacity = capacity
    client.app_service_plans.begin_create_or_update(resource_group, plan_name, plan).result()
    return {"action": "scale_app_service", "plan": plan_name, "sku": sku_name, "capacity": capacity}

def delete_resource(resource_id: str) -> dict:
    parts = resource_id.strip("/").split("/")
    rg = parts[parts.index("resourceGroups") + 1]
    _check_rg(rg)
    client = ResourceManagementClient(_credential(), SUBSCRIPTION_ID)
    client.resources.begin_delete_by_id(resource_id, api_version="2021-04-01").result()
    return {"action": "delete_resource", "resource_id": resource_id, "status": "deleted"}