from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.appcontainers import ContainerAppsAPIClient
import os

from state.session_store import get_credential, get_subscription_id

ALLOWED_RGS = set(os.getenv("AZURE_ALLOWED_RGS", "rg-finops-prod,rg-finopsai-dev").split(","))

def _credential():
    credential = get_credential()
    if credential is None:
        raise ValueError("Azure credentials are not configured")
    return credential

def _subscription_id():
    subscription_id = get_subscription_id()
    if not subscription_id:
        raise ValueError("Azure subscription ID is not configured")
    return subscription_id

def _check_rg(resource_group: str):
    if resource_group not in ALLOWED_RGS:
        raise ValueError(f"Resource group '{resource_group}' not in allowed list.")

def apply_tags(resource_id: str, tags: dict) -> dict:
    cred = _credential()
    client = ResourceManagementClient(cred, _subscription_id())
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
    client = ComputeManagementClient(_credential(), _subscription_id())
    client.virtual_machines.begin_deallocate(resource_group, vm_name).result()
    return {"action": "stop_vm", "vm": vm_name, "status": "deallocated"}

def start_vm(resource_group: str, vm_name: str) -> dict:
    _check_rg(resource_group)
    client = ComputeManagementClient(_credential(), _subscription_id())
    client.virtual_machines.begin_start(resource_group, vm_name).result()
    return {"action": "start_vm", "vm": vm_name, "status": "started"}

def scale_app_service(resource_group: str, plan_name: str, sku_name: str, capacity: int) -> dict:
    _check_rg(resource_group)
    client = WebSiteManagementClient(_credential(), _subscription_id())
    plan = client.app_service_plans.get(resource_group, plan_name)
    plan.sku.name = sku_name
    plan.sku.capacity = capacity
    client.app_service_plans.begin_create_or_update(resource_group, plan_name, plan).result()
    return {"action": "scale_app_service", "plan": plan_name, "sku": sku_name, "capacity": capacity}


def _strip_sensitive(app) -> None:
    if app.configuration:
        app.configuration.secrets = None
        app.configuration.registries = None
    if app.template and app.template.containers:
        for container in app.template.containers:
            if container.env:
                container.env = [e for e in container.env if not e.secret_ref]

def stop_container_app(resource_group: str, app_name: str) -> dict:
    _check_rg(resource_group)
    client = ContainerAppsAPIClient(_credential(), _subscription_id())
    app = client.container_apps.get(resource_group, app_name)
    app.template.scale.min_replicas = 0
    app.template.scale.max_replicas = 1
    _strip_sensitive(app)
    client.container_apps.begin_create_or_update(resource_group, app_name, app).result()
    return {"action": "stop_container_app", "app": app_name, "status": "stopped"}

def start_container_app(resource_group: str, app_name: str, max_replicas: int = 1) -> dict:
    _check_rg(resource_group)
    client = ContainerAppsAPIClient(_credential(), _subscription_id())
    app = client.container_apps.get(resource_group, app_name)
    app.template.scale.min_replicas = 1
    app.template.scale.max_replicas = max_replicas
    _strip_sensitive(app)
    client.container_apps.begin_create_or_update(resource_group, app_name, app).result()
    return {"action": "start_container_app", "app": app_name, "status": "started", "max_replicas": max_replicas}
def delete_resource(resource_id: str) -> dict:
    parts = resource_id.strip("/").split("/")
    rg = parts[parts.index("resourceGroups") + 1]
    _check_rg(rg)
    client = ResourceManagementClient(_credential(), _subscription_id())
    client.resources.begin_delete_by_id(resource_id, api_version="2021-04-01").result()
    return {"action": "delete_resource", "resource_id": resource_id, "status": "deleted"}
